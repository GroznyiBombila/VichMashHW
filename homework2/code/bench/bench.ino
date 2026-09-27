/*
 * Замер скорости процессора.
 * Один и тот же файл прошивается и в Arduino Nano, и в обе ESP32 —
 * различия спрятаны в нескольких #if, сами тесты общие.
 *
 * Результат печатается в монитор порта (115200) строками CSV:
 *   плата;тест;операций;время_мкс;тактов_на_операцию
 * Их можно скопировать прямо в Excel и построить графики.
 *
 * Тесты:
 *   1) цена одной арифметической операции для разных типов;
 *   2) цена вызова функции: одиночный вызов и глубокая рекурсия;
 *   3) множество Мандельброта дробными числами и целыми;
 *   4) чтение памяти с разным шагом: SRAM, PSRAM (это DRAM), флеш;
 *   5) EEPROM — только Nano: запись в ППЗУ против записи в ОЗУ;
 *   6) смена частоты 80/160/240 МГц — только ESP32:
 *      арифметика ускоряется вместе с ядром, а внешняя память нет.
 */

#if defined(ARDUINO_ARCH_AVR)
  #include <avr/pgmspace.h>
  #include <EEPROM.h>
  const char BOARD_NAME[] = "nano";
  float cpuMHz = 16.0;
#else
  #include <WiFi.h>
  const char BOARD_NAME[] = "esp32";
  float cpuMHz = 240.0;          // уточняется в setup()
#endif

// Куда складываются результаты вычислений.
// Без volatile компилятор увидит, что результат никому не нужен,
// и выбросит весь тест — время получится нулевым.
volatile int32_t sinkInt = 0;
volatile float   sinkFloat = 0;
volatile double  sinkDouble = 0;

// Исходные данные тоже volatile, иначе они посчитаются при компиляции.
volatile int8_t  a8 = 3,      b8 = 7;
volatile int32_t a32 = 12345, b32 = 67;
volatile float   af = 1.234f, bf = 5.678f;
volatile double  ad = 1.234,  bd = 5.678;

// Печать конца строки результата: число операций, время и такты.
void reportNumbers(uint32_t ops, uint32_t us) {
  float perOp = (float)us * cpuMHz / (float)ops;   // тактов на одну операцию
  Serial.print(';');
  Serial.print(ops);        Serial.print(';');
  Serial.print(us);         Serial.print(';');
  Serial.println(perOp, 2);
}

// Печать одной строки результата. Две версии: имя теста — обычная строка
// или строка во флеше. F("...") держит текст во флеше, а не в ОЗУ:
// у Nano всего 2 КБ ОЗУ, и каждое имя теста там было бы на счету.
void report(const char* test, uint32_t ops, uint32_t us) {
  Serial.print(BOARD_NAME); Serial.print(';');
  Serial.print(test);
  reportNumbers(ops, us);
}

void report(const __FlashStringHelper* test, uint32_t ops, uint32_t us) {
  Serial.print(BOARD_NAME); Serial.print(';');
  Serial.print(test);
  reportNumbers(ops, us);
}

// ---------- Тест 1: цена одной операции ----------------------------
// В каждом цикле выполняется ровно одна операция нужного типа.
// Первый замер — цикл без арифметики, его время потом вычитается.

void testOperations() {
  const uint32_t N = 20000;
  uint32_t t;

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkInt = a32;          // только пересылка
  report(F("op_empty"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkInt = a8 + b8;      // 8 бит
  report(F("op_add8"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkInt = a32 + b32;    // 32 бита
  report(F("op_add32"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkInt = a32 * b32;
  report(F("op_mul32"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkInt = a32 / b32;
  report(F("op_div32"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkFloat = af + bf;    // дробные
  report(F("op_addf"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkFloat = af * bf;
  report(F("op_mulf"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkFloat = af / bf;
  report(F("op_divf"), N, micros() - t);

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkDouble = ad * bd;   // двойная точность
  report(F("op_muld"), N, micros() - t);
}

// ---------- Тест 2: цена вызова функции ----------------------------
// У Nano при вызове адрес возврата и регистры кладутся в стек (PUSH/POP).
// У ESP32 вместо этого сдвигается «окно» регистров, и в стек процессор
// лезет, только когда окна кончились — то есть при глубокой рекурсии.

// noinline запрещает компилятору вставить тело функции на место вызова
__attribute__((noinline)) int32_t addCall(int32_t a, int32_t b) {
  return a + b;
}

// Рекурсия глубиной depth. Запись в sinkInt после вызова не даёт
// компилятору превратить рекурсию в обычный цикл.
__attribute__((noinline)) int32_t chain(int depth) {
  if (depth == 0) return 0;
  int32_t r = chain(depth - 1);
  sinkInt = r;
  return r + 1;
}

void testCalls() {
  const uint32_t N = 20000;
  uint32_t t;

  t = micros();
  for (uint32_t i = 0; i < N; i++) sinkInt = addCall(a32, b32);
  report(F("call_flat"), N, micros() - t);

  const int DEPTH = 40;            // глубже, чем помещается в окна регистров ESP32
  const uint32_t REPEATS = 500;
  t = micros();
  for (uint32_t r = 0; r < REPEATS; r++) chain(DEPTH);
  report(F("call_deep"), REPEATS * DEPTH, micros() - t);
}

// ---------- Тест 3: множество Мандельброта -------------------------
// Считается картинка 48x16 точек, для каждой до 50 шагов z = z*z + c.
// Возвращается сумма шагов — только чтобы результат нельзя было выбросить.

const int MANDEL_W = 48, MANDEL_H = 16, MANDEL_MAX = 50;

uint32_t mandelbrotFloat() {
  uint32_t total = 0;
  for (int y = 0; y < MANDEL_H; y++) {
    for (int x = 0; x < MANDEL_W; x++) {
      float cr = -2.0f + 3.0f * x / MANDEL_W;
      float ci = -1.2f + 2.4f * y / MANDEL_H;
      float zr = 0, zi = 0;
      int steps = 0;
      while (steps < MANDEL_MAX && zr * zr + zi * zi < 4.0f) {
        float next = zr * zr - zi * zi + cr;
        zi = 2 * zr * zi + ci;
        zr = next;
        steps++;
      }
      total += steps;
    }
  }
  return total;
}

// То же самое целыми числами в формате 8.8:
// младшие 8 бит числа — дробная часть, то есть единица записывается как 256.
uint32_t mandelbrotFixed() {
  const int16_t FOUR = 4 * 256;
  uint32_t total = 0;
  for (int y = 0; y < MANDEL_H; y++) {
    for (int x = 0; x < MANDEL_W; x++) {
      int16_t cr = -512 + (int16_t)(768L * x / MANDEL_W);   // от -2.0 до 1.0
      int16_t ci = -307 + (int16_t)(614L * y / MANDEL_H);   // от -1.2 до 1.2
      int16_t zr = 0, zi = 0;
      int steps = 0;
      while (steps < MANDEL_MAX) {
        int16_t zr2 = (int16_t)(((int32_t)zr * zr) >> 8);   // умножение в 8.8
        int16_t zi2 = (int16_t)(((int32_t)zi * zi) >> 8);
        if (zr2 + zi2 >= FOUR) break;
        int16_t next = zr2 - zi2 + cr;
        zi = (int16_t)((((int32_t)zr * zi) >> 8) * 2 + ci);
        zr = next;
        steps++;
      }
      total += steps;
    }
  }
  return total;
}

void testMandelbrot() {
  const uint32_t points = (uint32_t)MANDEL_W * MANDEL_H;
  uint32_t t;

  t = micros();
  sinkInt = mandelbrotFloat();
  report(F("mandel_float"), points, micros() - t);

  t = micros();
  sinkInt = mandelbrotFixed();
  report(F("mandel_fixed"), points, micros() - t);
}

// ---------- Тест 4: чтение памяти с разным шагом --------------------
// Пока шаг меньше строки кэша, соседние байты уже привезены и читаются
// быстро. Когда шаг перерастает строку, каждое чтение идёт в память.
//
// У ESP32 через кэш идут только флеш и PSRAM, внутренняя SRAM читается
// напрямую. PSRAM — это DRAM (конденсаторы с регенерацией) с интерфейсом
// как у SRAM, поэтому ESP32-CAM сравнивает SRAM и DRAM на одном чипе.
// У Nano кэша нет, время не должно зависеть от шага.

#if defined(ARDUINO_ARCH_AVR)
  // таблица во флеше: у AVR её нельзя прочитать обычным указателем
  const uint8_t flashTable[1024] PROGMEM = { 1 };
#else
  // у ESP32 флеш отображён в адреса и читается как обычный массив
  const uint8_t flashTable[64 * 1024] = { 1 };
#endif

// Сколько раз пройти буфер, чтобы замер длился заметное время.
uint32_t passesFor(size_t size) {
  return 2000000UL / size + 1;
}

// Проход по буферу в ОЗУ (или во флеше ESP32) с шагом step, время в мкс.
uint32_t readStride(const uint8_t* buf, size_t size, size_t step, uint32_t passes) {
  uint32_t sum = 0;
  uint32_t t = micros();
  for (uint32_t p = 0; p < passes; p++)
    for (size_t i = 0; i < size; i += step) sum += buf[i];
  uint32_t us = micros() - t;
  sinkInt = sum;
  return us;
}

#if defined(ARDUINO_ARCH_AVR)
// То же для флеша Nano: каждое чтение — отдельная команда pgm_read_byte.
uint32_t readStrideFlashAvr(size_t size, size_t step, uint32_t passes) {
  uint32_t sum = 0;
  uint32_t t = micros();
  for (uint32_t p = 0; p < passes; p++)
    for (size_t i = 0; i < size; i += step) sum += pgm_read_byte(&flashTable[i]);
  uint32_t us = micros() - t;
  sinkInt = sum;
  return us;
}
#endif

// Прогон всех шагов от 1 до 128 для одного вида памяти.
void strideSweep(const char* where, const uint8_t* buf, size_t size, bool avrFlash) {
  for (size_t step = 1; step <= 128; step *= 2) {
    uint32_t passes = passesFor(size);
    uint32_t us;
#if defined(ARDUINO_ARCH_AVR)
    if (avrFlash) us = readStrideFlashAvr(size, step, passes);
    else          us = readStride(buf, size, step, passes);
#else
    us = readStride(buf, size, step, passes);
#endif
    char name[24];
    sprintf(name, "mem_%s_step%u", where, (unsigned)step);
    report(name, passes * (uint32_t)(size / step), us);
  }
}

void testMemory() {
#if defined(ARDUINO_ARCH_AVR)
  static uint8_t ram[1024];              // больше в 2 КБ ОЗУ не влезет
  for (size_t i = 0; i < sizeof(ram); i++) ram[i] = (uint8_t)i;
  strideSweep("sram", ram, sizeof(ram), false);
  strideSweep("flash", nullptr, sizeof(flashTable), true);
#else
  const size_t SRAM_SIZE = 32UL * 1024UL;          // внутренняя SRAM
  uint8_t* sram = (uint8_t*)malloc(SRAM_SIZE);
  if (sram) {
    for (size_t i = 0; i < SRAM_SIZE; i++) sram[i] = (uint8_t)i;
    strideSweep("sram", sram, SRAM_SIZE, false);
    free(sram);
  }

  const size_t PSRAM_SIZE = 1024UL * 1024UL;       // внешняя PSRAM, есть только у ESP32-CAM
  uint8_t* psram = (uint8_t*)ps_malloc(PSRAM_SIZE);
  if (psram) {
    for (size_t i = 0; i < PSRAM_SIZE; i++) psram[i] = (uint8_t)i;
    strideSweep("psram", psram, PSRAM_SIZE, false);
    free(psram);
  } else {
    Serial.println(F("# PSRAM нет — для ЙоТика это нормально"));
  }

  strideSweep("flash", flashTable, sizeof(flashTable), false);
#endif
}

// ---------- Тест 5: EEPROM (только Nano) ---------------------------
// EEPROM — перепрограммируемое ПЗУ внутри ATmega328P. Данные в нём
// сохраняются без питания, но запись одного байта идёт миллисекунды.
// Ячейка выдерживает около 100 000 записей, поэтому тест пишет всего
// 32 байта за запуск — прошивку можно перезапускать спокойно.

#if defined(ARDUINO_ARCH_AVR)
void testEeprom() {
  const int BYTES = 32;
  static volatile uint8_t ramCopy[BYTES];
  uint32_t t;

  t = micros();
  for (int i = 0; i < BYTES; i++) EEPROM.write(i, (uint8_t)i);
  eeprom_busy_wait();      // дождаться конца последней записи, иначе её ждало бы чтение
  report(F("eeprom_write"), BYTES, micros() - t);

  uint32_t sum = 0;
  t = micros();
  for (int i = 0; i < BYTES; i++) sum += EEPROM.read(i);
  report(F("eeprom_read"), BYTES, micros() - t);
  sinkInt = sum;

  t = micros();
  for (int i = 0; i < BYTES; i++) ramCopy[i] = (uint8_t)i;   // для сравнения
  report(F("sram_write"), BYTES, micros() - t);
}
#endif

// ---------- Тест 6: смена частоты (только ESP32) --------------------
// Это ручной Turbo Boost: частоту ядра меняет сама программа.
// Здесь важна колонка время_мкс. Арифметика и SRAM работают на частоте
// ядра и должны ускориться втрое. PSRAM и флеш тактируются отдельно,
// поэтому при промахе кэша ядро ждёт их одинаково долго на любой частоте.

#if !defined(ARDUINO_ARCH_AVR)
void testFrequency() {
  const int freqs[] = { 80, 160, 240 };
  const uint32_t N = 20000;
  const size_t STEP = 64;                 // шаг больше строки кэша: каждое чтение — промах
  uint8_t* psram = (uint8_t*)ps_malloc(1024UL * 1024UL);
  uint8_t* sram = (uint8_t*)malloc(32UL * 1024UL);

  for (int f = 0; f < 3; f++) {
    setCpuFrequencyMhz(freqs[f]);
    cpuMHz = getCpuFrequencyMhz();
    delay(100);
    char name[24];
    uint32_t t;

    t = micros();
    for (uint32_t i = 0; i < N; i++) sinkInt = a32 + b32;
    sprintf(name, "f%d_add32", freqs[f]);
    report(name, N, micros() - t);

    if (sram) {
      uint32_t passes = passesFor(32UL * 1024UL);
      sprintf(name, "f%d_sram", freqs[f]);
      report(name, passes * (32UL * 1024UL / STEP), readStride(sram, 32UL * 1024UL, STEP, passes));
    }
    if (psram) {
      uint32_t passes = passesFor(1024UL * 1024UL);
      sprintf(name, "f%d_psram", freqs[f]);
      report(name, passes * (1024UL * 1024UL / STEP), readStride(psram, 1024UL * 1024UL, STEP, passes));
    }
    uint32_t passes = passesFor(sizeof(flashTable));
    sprintf(name, "f%d_flash", freqs[f]);
    report(name, passes * (sizeof(flashTable) / STEP), readStride(flashTable, sizeof(flashTable), STEP, passes));
  }

  free(sram);
  free(psram);
  setCpuFrequencyMhz(240);
  cpuMHz = getCpuFrequencyMhz();
}
#endif

// ---------- Запуск --------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(1000);

#if !defined(ARDUINO_ARCH_AVR)
  WiFi.mode(WIFI_OFF);     // радио мешает замерам: прерывания и своё ядро
  btStop();
  cpuMHz = getCpuFrequencyMhz();
#endif

  Serial.println();
  Serial.print(F("# плата: ")); Serial.print(BOARD_NAME);
  Serial.print(F("  частота: ")); Serial.print(cpuMHz); Serial.println(F(" МГц"));
  Serial.println(F("плата;тест;операций;время_мкс;тактов_на_операцию"));

  testOperations();
  testCalls();
  testMandelbrot();
  testMemory();
#if defined(ARDUINO_ARCH_AVR)
  testEeprom();
#else
  testFrequency();
#endif

  Serial.println(F("# готово"));
}

void loop() {
}

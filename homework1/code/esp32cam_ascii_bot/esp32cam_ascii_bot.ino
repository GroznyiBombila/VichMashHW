/* =============================================================================
 *  ESP32-CAM  ->  OLED SSD1306 128x64  ->  Telegram (псевдографика)
 * -----------------------------------------------------------------------------
 *  Что делает:
 *    - при старте рисует белую полосу на дисплее (признак "питание есть, I2C жив")
 *    - в loop() непрерывно показывает картинку с камеры на OLED (дизеринг Аткинсона)
 *    - по нажатию кнопки: снимок -> показ снимка -> ASCII-арт -> Telegram
 *
 *  Плата: AI-Thinker ESP32-CAM, камера OV2640, формат кадра GRAYSCALE 160x120.
 *  Библиотеки (Менеджер библиотек): Adafruit GFX Library, Adafruit SSD1306.
 *  Плата в IDE: "AI Thinker ESP32-CAM", PSRAM: Enabled.
 *
 *  ПОДКЛЮЧЕНИЕ:
 *    OLED SDA -> GPIO14      OLED SCL -> GPIO13      OLED VCC -> 3V3, GND -> GND
 *    Кнопка снимка: один вывод -> GPIO2, второй -> GND (подтяжка внутренняя)
 *    Кнопка сброса: RST <-> GND (тактовая, пригодится после снятия программатора)
 *    Вспышка на GPIO4 не используется: пин прижат к земле, светодиод погашен
 *
 *    GPIO12 НЕ ИСПОЛЬЗОВАТЬ - strapping-пин, подтяжка к 3.3В = плата не загрузится.
 *    GPIO16 НЕ ИСПОЛЬЗОВАТЬ - занят PSRAM.
 * ========================================================================== */

#include "esp_camera.h"        // работа с камерой
#include <WiFi.h>              // подключение к сети
#include <WiFiClientSecure.h>  // HTTPS (Telegram работает только по HTTPS)
#include <HTTPClient.h>        // удобная обёртка над HTTP-запросом
#include <Wire.h>              // шина I2C для дисплея
#include <Adafruit_GFX.h>      // графическое ядро (drawBitmap, шрифт)
#include <Adafruit_SSD1306.h>  // драйвер контроллера дисплея
#include <WebServer.h>         // свой веб-сервер: показ арта без интернета


/* =============================================================================
 *  БЛОК 1. НАСТРОЙКИ. Здесь всё, что ты будешь менять руками.
 * ========================================================================== */

/* ---- Сеть и бот. Подставь свои значения ---------------------------------- */
#define WIFI_SSID      "ИМЯ_СЕТИ"          // ESP32 умеет только 2.4 ГГц, не 5 ГГц!
#define WIFI_PASS      "ПАРОЛЬ_СЕТИ"
#define TG_BOT_TOKEN   "123456789:AAAA..." // токен от @BotFather
#define TG_CHAT_ID     "123456789"         // твой личный chat_id

/* ---- Пины ---------------------------------------------------------------- */
/* --- Своя точка доступа для показа без интернета --------------------------
 * Плата поднимает собственный WiFi. Подключаешься к нему телефоном,
 * открываешь http://192.168.4.1 - и видишь живую картинку в браузере.
 * Интернет для этого не нужен вообще: ни мобильный, ни какой.
 * Работает одновременно с обычным подключением к роутеру.               */
#define AP_SSID        "ESP32-CAM-ART"   // имя сети, которую раздаёт плата
#define AP_PASS        "12345678"        // пароль, минимум 8 символов
#define WEB_PORT       80

#define PIN_OLED_SDA   14
#define PIN_OLED_SCL   13
#define PIN_BUTTON      2                  // кнопка снимка, замыкает на GND
#define PIN_FLASH       4                  // штатный белый светодиод-вспышка

/* ---- Дисплей ------------------------------------------------------------- */
#define OLED_W        128
#define OLED_H         64
#define OLED_ADDR    0x3C                  // у части модулей 0x3D
#define OLED_BYTES  (OLED_W * OLED_H / 8)  // 1024 байта: 1 бит на пиксель

/* ---- Камера -------------------------------------------------------------- */
#define CAM_W         160                  // FRAMESIZE_QQVGA
#define CAM_H         120
#define CAM_VFLIP       0                  // 1 = перевернуть по вертикали
#define CAM_HMIRROR     1                  // 1 = зеркалить по горизонтали
/* Подбирается опытным путём, всего четыре сочетания. Наведи камеру на текст:
 *   текст читается нормально          - оставляй как есть
 *   текст вверх ногами (поворот 180)  - поменяй ОБА значения на противоположные
 *   текст зеркальный, строки на месте - поменяй только CAM_HMIRROR
 *   текст стоит на голове, но не зеркальный - поменяй только CAM_VFLIP        */

/* ---- Кроп для дисплея ----------------------------------------------------
 * Дисплей 128x64 это соотношение 2:1, а кадр камеры 160x120 это 4:3.
 * Поэтому берём из кадра горизонтальную полосу 160x80 по центру.
 * Совет из практики: наводи так, чтобы в полосу попало от бровей до подбородка -
 * лицо целиком в 2:1 не влезает и займёт лишь треть экрана.                  */
#define CROP_W        160
#define CROP_H         80
#define CROP_X          0                  // (CAM_W - CROP_W) / 2
#define CROP_Y         20                  // (CAM_H - CROP_H) / 2

/* ---- Псевдографика для Telegram ------------------------------------------
 * Здесь кроп НЕ нужен: берём весь кадр 160x120, иначе арт выйдет узкой полоской.
 *
 * Символ в <pre>-блоке Telegram примерно в 2.2 раза выше своей ширины, поэтому
 * высота считается от ширины, чтобы картинка не сплющилась:
 *   ширина ячейки = 160 / ART_W пикселей
 *   высота ячейки = ширина * 2.2
 *   ART_H         = 120 / высота ячейки
 *
 * Готовые пары, выбирай по тому, где смотришь арт:
 *   ART_W 32, ART_H 11  -   352 символа: влезает в любой телефон, но лицо - каша
 *   ART_W 40, ART_H 13  -   520 символов
 *   ART_W 48, ART_H 16  -   768 символов: компьютер и большинство телефонов
 *   ART_W 64, ART_H 22  -  1408 символов: чётко, но на телефоне строки переносятся
 *
 * Если на телефоне строки арта ломаются пополам - уменьши на одну ступень.   */
#define ART_W          48
#define ART_H          16
#define ART_BUF_LEN   (ART_H * (ART_W + 1) + 1)   // +1 на '\n' в строке, +1 на конец

/* Рампа: от самого плотного символа к самому пустому. */
#define ART_RAMP      "@%#*+=-:. "
#define ART_RAMP_LEN  10

/* Тёмная тема Telegram: фон тёмный, символы светлые, значит светлое место
 * фотографии должно давать ПЛОТНЫЙ символ. Для светлой темы поставь 0.        */
#define TG_INVERT       1

/* ---- Прочая подстройка --------------------------------------------------- */
#define PHOTO_HOLD_MS      3000   // сколько держать снимок на экране
#define BUTTON_DEBOUNCE_MS   50   // защита от дребезга контактов

/* ---- Wi-Fi и реконнект --------------------------------------------------- */
#define WIFI_TIMEOUT_MS        15000   // сколько ждать сеть при первом запуске
#define WIFI_RETRY_INTERVAL_MS 10000   // как часто пробовать переподключиться в фоне
#define WIFI_RETRY_TIMEOUT_MS   8000   // сколько ждать сеть непосредственно перед
                                       // отправкой (тут ждём блокирующе)

/* ---- Как ходить в Telegram ------------------------------------------------
 *  0 = напрямую в api.telegram.org по HTTPS. Так задумано у Telegram, но
 *      многие сети этот адрес просто не пускают - мы это уже проверили.
 *
 *  1 = через свой VPS. На сервере стоит перенаправитель: плата шлёт ему
 *      обычный HTTP-запрос, а он переписывает его в Telegram по HTTPS и
 *      возвращает ответ обратно. Для платы это тот же самый Bot API,
 *      меняется только адрес - поэтому весь остальной код не тронут.
 *
 *  Побочный плюс: обычный HTTP плате даётся куда легче, чем HTTPS.
 *  Шифрование съедает около 40 КБ оперативной памяти и заметное время
 *  на рукопожатие, а тут этим занимается сервер.                          */
#define TG_VIA_PROXY     1
#define TG_PROXY_HOST    "ВАШ_IP"         // адрес своего VPS
#define TG_PROXY_PORT    8099             // порт, который слушает перенаправитель


/* =============================================================================
 *  БЛОК 2. РАСПИНОВКА КАМЕРЫ. Не трогать - это жёстко разведено на плате.
 * ========================================================================== */
#define PWDN_GPIO_NUM    32
#define RESET_GPIO_NUM   -1
#define XCLK_GPIO_NUM     0
#define SIOD_GPIO_NUM    26
#define SIOC_GPIO_NUM    27
#define Y9_GPIO_NUM      35
#define Y8_GPIO_NUM      34
#define Y7_GPIO_NUM      39
#define Y6_GPIO_NUM      36
#define Y5_GPIO_NUM      21
#define Y4_GPIO_NUM      19
#define Y3_GPIO_NUM      18
#define Y2_GPIO_NUM       5
#define VSYNC_GPIO_NUM   25
#define HREF_GPIO_NUM    23
#define PCLK_GPIO_NUM    22


/* =============================================================================
 *  БЛОК 3. ГЛОБАЛЬНЫЕ БУФЕРЫ И ОБЪЕКТЫ
 * -----------------------------------------------------------------------------
 *  Все буферы статические, фиксированного размера. Никаких malloc - на
 *  микроконтроллере это надёжнее: память выделяется один раз при компиляции,
 *  и ты сразу видишь, сколько её уходит.
 * ========================================================================== */

// Дисплей. -1 означает "пина сброса нет", у I2C-модулей его и не бывает.
Adafruit_SSD1306 display(OLED_W, OLED_H, &Wire, -1);

static uint8_t  grayForOled[OLED_W * OLED_H];  //  8 КБ: полутона 128x64, 0..255
static int16_t  ditherWork[OLED_W * OLED_H];   // 16 КБ: рабочая копия для дизеринга.
                                               // int16, а не uint8, потому что при
                                               // разносе ошибки значение временно
                                               // вылезает за пределы 0..255
static uint8_t  oledBitmap[OLED_BYTES];        //  1 КБ: итог, 1 бит на пиксель
static uint8_t  artCells[ART_W * ART_H];       // полутона под сетку символов
static char     asciiArt[ART_BUF_LEN];         // готовый текст арта
static char     lastPhotoArt[ART_BUF_LEN];     // арт последнего СНИМКА (по кнопке)
static uint32_t photoCounter = 0;              // сколько снимков сделано

/* Таблицы гамма-коррекции. Зачем: значения пикселя в sRGB нелинейны, а
 * усреднять физически надо линейную яркость. Без этого детализированные места
 * (волосы, ткань, листва) систематически выходят темнее, чем на самом деле.
 * Считаем таблицы один раз в setup(): powf() на каждый из 8192 пикселей
 * в каждом кадре - это заметная потеря скорости.                             */
static uint16_t gammaToLinear[256];   // байт sRGB      -> линейная яркость 0..65535
static uint8_t  linearToGamma[256];   // линейная >> 8  -> байт sRGB

static int lastHttpCode = 0;          // код ответа Telegram, показываем на экране


/* =============================================================================
 *  БЛОК 4. ДИСПЛЕЙ: инициализация, стартовая полоса, текстовый статус
 * ========================================================================== */

void initDisplay() {
  Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL);

  /* Четвёртый аргумент false - "не вызывай Wire.begin() сам".
   * По умолчанию библиотека делает это с пинами по умолчанию (21/22) и может
   * затереть наши 14/13. Классическая причина "дисплей не отвечает".         */
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR, true, false)) {
    Serial.println("OLED не найден. Проверь адрес (0x3C/0x3D) и пины 14/13.");
    while (true) { delay(1000); }   // дальше идти смысла нет
  }

  /* 400 кГц вместо стандартных 100 кГц. Полный кадр это 1024 байта:
   * на 100 кГц отправка занимает ~92 мс (11 fps), на 400 кГц ~23 мс (43 fps).
   * Ставим ПОСЛЕ begin(), потому что begin() сбрасывает частоту.             */
  Wire.setClock(400000);

  display.clearDisplay();
  display.display();
}

/* Белая полоса при включении: проезжает слева направо по центру экрана.
 * Это одновременно и "питание подано", и проверка, что I2C реально работает. */
void showStartupBar() {
  for (int x = 0; x <= OLED_W; x += 4) {
    display.clearDisplay();
    display.fillRect(0, OLED_H / 2 - 4, x, 8, SSD1306_WHITE);
    display.display();
  }
  delay(200);
  display.clearDisplay();
  display.display();
}

/* Короткое сообщение по центру экрана: WiFi, Sending, OK, ошибки.
 * Без такой обратной связи отладка идёт вслепую - непонятно, кто виноват:
 * сеть, токен или камера.                                                    */
void showStatus(const char *text) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(2, OLED_H / 2 - 4);
  display.println(text);
  display.display();
}

/* Вывод готового 1-битного битмапа на экран.
 * warnNoWifi = true рисует поверх картинки мигающий квадратик в правом верхнем
 * углу: сети сейчас нет. Индикатор рисуется ДО display.display(), то есть
 * бесплатно - лишней передачи кадра по I2C не происходит.
 * Квадратик белый в чёрной рамке, чтобы он был виден и на светлом фоне.      */
void drawOledBitmap(const uint8_t *bitmap, bool warnNoWifi) {
  display.clearDisplay();   // drawBitmap рисует только единичные биты,
                            // нулевые он не стирает - поэтому чистим сами
  display.drawBitmap(0, 0, bitmap, OLED_W, OLED_H, SSD1306_WHITE);

  if (warnNoWifi && (millis() / 500) % 2 == 0) {   // мигание раз в полсекунды
    display.fillRect(OLED_W - 8, 0, 8, 8, SSD1306_BLACK);   // тёмная подложка
    display.fillRect(OLED_W - 7, 1, 6, 6, SSD1306_WHITE);   // сам маркер
  }

  display.display();
}


/* =============================================================================
 *  БЛОК 5. КАМЕРА
 * ========================================================================== */

bool initCamera() {
  camera_config_t config;

  config.ledc_channel = LEDC_CHANNEL_0;   // канал ШИМ под тактовый сигнал XCLK
  config.ledc_timer   = LEDC_TIMER_0;     // (запомни: канал 0 занят камерой)
  config.pin_d0 = Y2_GPIO_NUM;   config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;   config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;   config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;   config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk  = XCLK_GPIO_NUM;    config.pin_pclk  = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;   config.pin_href  = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM; // отдельная от нашей шина I2C камеры,
  config.pin_sccb_scl = SIOC_GPIO_NUM; // с дисплеем на 14/13 не конфликтует
  // Если компилятор ругается на pin_sccb_sda - у тебя старая версия ядра,
  // тогда поля называются pin_sscb_sda / pin_sscb_scl (через "ss").
  config.pin_pwdn  = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;

  /* Ключевой момент всего проекта: GRAYSCALE.
   * Камера отдаёт готовый массив яркостей, по байту на пиксель.
   * Никакого JPEG-декодера не нужно - именно он был бы главной проблемой.
   * 160*120 = 19200 байт на кадр.                                            */
  config.pixel_format = PIXFORMAT_GRAYSCALE;
  config.frame_size   = FRAMESIZE_QQVGA;

  config.fb_count     = 1;
  config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location  = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.jpeg_quality = 12;   // в grayscale не используется, но поле заполнить надо

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Камера не инициализировалась, код 0x%x\n", err);
    return false;
  }

  // Ориентация. Настраивается уже после запуска, через объект сенсора.
  sensor_t *s = esp_camera_sensor_get();
  s->set_vflip(s, CAM_VFLIP);
  s->set_hmirror(s, CAM_HMIRROR);

  return true;
}


/* =============================================================================
 *  БЛОК 6. ВСПЫШКА - УБРАНА
 * -----------------------------------------------------------------------------
 *  Белый светодиод на GPIO4 больше не используется. Пин один раз переводится
 *  в выход и прижимается к земле в самом начале setup(), и таким остаётся
 *  до выключения питания - светодиод не загорается никогда.
 *
 *  Заодно ушёл главный потребитель тока: на полной яркости этот светодиод
 *  брал 300-400 мА и на батарее ронял напряжение до перезагрузки платы.
 * ========================================================================== */


/* =============================================================================
 *  БЛОК 7. КНОПКА
 * -----------------------------------------------------------------------------
 *  INPUT_PULLUP: пин внутренне подтянут к 3.3В, кнопка замыкает его на землю.
 *  Значит НАЖАТА = LOW. Внешний резистор не нужен.
 *  Реагируем на фронт (переход отпущена -> нажата), а не на само состояние,
 *  иначе одно удержание кнопки отправит десяток сообщений подряд.
 * ========================================================================== */
bool buttonPressed() {
  static bool wasDown = false;
  bool isDown = (digitalRead(PIN_BUTTON) == LOW);

  if (isDown && !wasDown) {
    delay(BUTTON_DEBOUNCE_MS);              // пауза на успокоение контактов
    if (digitalRead(PIN_BUTTON) == LOW) {   // всё ещё нажата - значит не дребезг
      wasDown = true;
      return true;
    }
    return false;
  }
  if (!isDown) wasDown = false;             // отпустили, ждём нового фронта
  return false;
}


/* =============================================================================
 *  БЛОК 8. ОБРАБОТКА ИЗОБРАЖЕНИЯ
 * -----------------------------------------------------------------------------
 *  Конвейер целиком:
 *    кадр камеры -> box-даунскейл с гамма-коррекцией -> растяжка контраста
 *      -> ветка OLED:     дизеринг Аткинсона -> 1 бит на пиксель
 *      -> ветка Telegram: маппинг яркости в символы рампы
 * ========================================================================== */

/* Таблицы гаммы. Строятся один раз при запуске. */
void buildGammaTables() {
  for (int i = 0; i < 256; i++) {
    // sRGB -> линейная яркость. 2.2 - стандартный показатель гаммы.
    gammaToLinear[i] = (uint16_t)(powf(i / 255.0f, 2.2f) * 65535.0f + 0.5f);
    // Обратно. Индекс - старший байт линейного значения, точности хватает:
    // на выходе всё равно 1 бит на пиксель.
    linearToGamma[i] = (uint8_t)(powf(i / 255.0f, 1.0f / 2.2f) * 255.0f + 0.5f);
  }
}

/* Box-даунскейл: каждый пиксель результата = средняя яркость своего
 * прямоугольника в оригинале. Именно усреднение, а не выборка одного пикселя
 * (то есть не NEAREST) - иначе при сжатии 160 -> 32 выбрасывается 96% данных
 * и вместо картинки получается рваный шум.
 * Границы считаются целочисленно, поэтому дробный коэффициент (например 1.25)
 * обрабатывается сам собой: где-то в ячейку попадёт 1 пиксель, где-то 2.     */
void boxDownscale(const uint8_t *src, int srcStride,
                  int cropX, int cropY, int cropW, int cropH,
                  uint8_t *dst, int dstW, int dstH) {
  for (int dy = 0; dy < dstH; dy++) {
    int sy0 = cropY + (dy * cropH) / dstH;
    int sy1 = cropY + ((dy + 1) * cropH) / dstH;
    if (sy1 <= sy0) sy1 = sy0 + 1;                 // ячейка не может быть пустой

    for (int dx = 0; dx < dstW; dx++) {
      int sx0 = cropX + (dx * cropW) / dstW;
      int sx1 = cropX + ((dx + 1) * cropW) / dstW;
      if (sx1 <= sx0) sx1 = sx0 + 1;

      uint32_t sum = 0, count = 0;
      for (int sy = sy0; sy < sy1; sy++) {
        const uint8_t *row = src + sy * srcStride;
        for (int sx = sx0; sx < sx1; sx++) {
          sum += gammaToLinear[row[sx]];           // складываем ЛИНЕЙНУЮ яркость
          count++;
        }
      }
      uint32_t avgLinear = sum / count;                      // 0..65535
      dst[dy * dstW + dx] = linearToGamma[avgLinear >> 8];   // и обратно в sRGB
    }
  }
}

/* Растяжка контраста: самый тёмный пиксель становится 0, самый светлый 255.
 * Делается ПОСЛЕ уменьшения, а не до. Без неё тёмная комната отобразится
 * тремя символами рампы из десяти, и весь кадр будет однородным пятном.      */
void autoContrast(uint8_t *buf, int count) {
  uint8_t mn = 255, mx = 0;
  for (int i = 0; i < count; i++) {
    if (buf[i] < mn) mn = buf[i];
    if (buf[i] > mx) mx = buf[i];
  }
  if (mx - mn < 16) return;   // кадр почти однотонный (объектив закрыт, темнота) -
                              // растягивать нечего, иначе усилим один шум
  int range = mx - mn;
  for (int i = 0; i < count; i++) {
    buf[i] = (uint8_t)(((int)(buf[i] - mn) * 255) / range);
  }
}

/* Вспомогательная: добавить часть ошибки соседнему пикселю, если он существует. */
static inline void spreadError(int x, int y, int err) {
  if (x < 0 || x >= OLED_W || y < 0 || y >= OLED_H) return;
  ditherWork[y * OLED_W + x] += err;
}

/* Дизеринг Аткинсона.
 * Зачем: у нас 1 бит на пиксель. Простое сравнение "ярче/темнее 128" делает из
 * лица плоские бесформенные пятна - светотень, по которой лицо и узнаётся,
 * пропадает полностью. Дизеринг имитирует полутона узором точек: ошибку
 * округления он не выбрасывает, а раздаёт соседним ещё не обработанным пикселям.
 *
 * Почему именно Аткинсон, а не Флойд-Стайнберг:
 *   - все веса равны 1/8, поэтому вся математика это деление на 8, без умножений;
 *   - разносится только 6/8 ошибки, а не вся - контраст выше, света чище,
 *     на маленьком экране это читается заметно лучше.
 * Схема разноса (X - текущий пиксель, каждому соседу по 1/8 ошибки):
 *          X  1  1
 *       1  1  1
 *          1
 */
void ditherAtkinson(const uint8_t *gray, uint8_t *bitmap) {
  for (int i = 0; i < OLED_W * OLED_H; i++) ditherWork[i] = gray[i];
  memset(bitmap, 0, OLED_BYTES);

  for (int y = 0; y < OLED_H; y++) {
    for (int x = 0; x < OLED_W; x++) {
      int oldValue = ditherWork[y * OLED_W + x];
      int newValue = (oldValue < 128) ? 0 : 255;   // собственно квантование в 1 бит

      if (newValue) {
        // Формат Adafruit: байт = 8 пикселей по горизонтали, старший бит слева.
        bitmap[y * (OLED_W / 8) + (x >> 3)] |= (0x80 >> (x & 7));
      }

      int err = (oldValue - newValue) / 8;
      spreadError(x + 1, y,     err);
      spreadError(x + 2, y,     err);
      spreadError(x - 1, y + 1, err);
      spreadError(x,     y + 1, err);
      spreadError(x + 1, y + 1, err);
      spreadError(x,     y + 2, err);
    }
  }
}

/* Кадр камеры -> полутона 128x64 для дисплея (с кропом центральной полосы). */
void frameToOledGray(camera_fb_t *fb, uint8_t *dst) {
  boxDownscale(fb->buf, CAM_W, CROP_X, CROP_Y, CROP_W, CROP_H, dst, OLED_W, OLED_H);
  autoContrast(dst, OLED_W * OLED_H);
}

/* Кадр камеры -> текстовый ASCII-арт.
 * Здесь берём ВЕСЬ кадр 160x120, без кропа: иначе при 32 символах ширины
 * из полосы 2:1 вышло бы всего 7 строк - слишком мало, чтобы что-то разобрать. */
void frameToAscii(camera_fb_t *fb, char *out) {
  boxDownscale(fb->buf, CAM_W, 0, 0, CAM_W, CAM_H, artCells, ART_W, ART_H);
  autoContrast(artCells, ART_W * ART_H);

  const char *ramp = ART_RAMP;
  int pos = 0;
  for (int y = 0; y < ART_H; y++) {
    for (int x = 0; x < ART_W; x++) {
      uint8_t v = artCells[y * ART_W + x];
      /* Рампа идёт от плотного символа (индекс 0, '@') к пустому (последний
       * индекс, пробел). Значит чтобы место стало ПЛОТНЫМ, индекс нужен МАЛЫЙ.
       * Раньше формулы в ветках были перепутаны, и арт выходил негативом.     */
#if TG_INVERT
      // Тёмная тема: светлое место фото -> плотный символ, то есть малый индекс
      int idx = ((255 - v) * (ART_RAMP_LEN - 1)) / 255;
#else
      // Светлая тема: тёмное место фото -> плотный символ, то есть малый индекс
      int idx = (v * (ART_RAMP_LEN - 1)) / 255;
#endif
      out[pos++] = ramp[idx];
    }
    out[pos++] = '\n';
  }
  out[pos] = '\0';
}


/* =============================================================================
 *  БЛОК 9. WI-FI И ОТПРАВКА В TELEGRAM
 * ========================================================================== */

/* Первое подключение при запуске. Ждём блокирующе - на этом этапе всё равно
 * больше нечего делать. Если сеть не поднялась, работу НЕ останавливаем:
 * превью и снимки должны работать и без интернета, а реконнект подхватит
 * сеть позже сам.                                                            */
void connectWiFi() {
  showStatus("WiFi...");
  WiFi.mode(WIFI_STA);

  /* Штатный автореконнект драйвера: при обрыве SDK сам попробует вернуться.
   * Он покрывает большинство случаев (кратковременная помеха, перезагрузка
   * роутера), но иногда залипает - поэтому ниже есть ещё и своя проверка.    */
  WiFi.setAutoReconnect(true);
  WiFi.persistent(true);

  WiFi.begin(WIFI_SSID, WIFI_PASS);

  uint32_t started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < WIFI_TIMEOUT_MS) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("WiFi OK, IP: ");
    Serial.println(WiFi.localIP());
    showStatus("WiFi OK");
  } else {
    Serial.println("WiFi не подключился. Проверь, что сеть 2.4 ГГц.");
    showStatus("WiFi FAIL");
  }
  delay(800);
}

/* Фоновый реконнект. Вызывается из loop() на каждом кадре, но реальные
 * действия выполняет не чаще WIFI_RETRY_INTERVAL_MS. Важно, что функция
 * НИЧЕГО НЕ ЖДЁТ: дала команду на переподключение и сразу вышла - иначе
 * живое превью замирало бы на несколько секунд при каждой попытке.
 *
 * disconnect(false, false) перед begin() нужен, чтобы сбросить залипшее
 * состояние драйвера. Аргументы: не выключать радио, не стирать сохранённые
 * настройки сети.                                                            */
void wifiKeepAlive() {
  static uint32_t lastTry = 0;

  if (WiFi.status() == WL_CONNECTED) return;              // всё в порядке
  if (millis() - lastTry < WIFI_RETRY_INTERVAL_MS) return; // рано, ждём

  lastTry = millis();
  Serial.println("WiFi потерян - пробую переподключиться");
  WiFi.disconnect(false, false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
}

/* Блокирующая попытка поднять сеть прямо сейчас. Используется только перед
 * отправкой в Telegram: там пользователь стоит и смотрит на экран, короткое
 * ожидание уместно, а вот отправка без сети смысла не имеет.                 */
bool ensureWiFi(uint32_t timeoutMs) {
  if (WiFi.status() == WL_CONNECTED) return true;

  showStatus("WiFi retry...");
  WiFi.disconnect(false, false);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  uint32_t started = millis();
  while (WiFi.status() != WL_CONNECTED && millis() - started < timeoutMs) {
    delay(200);
  }
  return (WiFi.status() == WL_CONNECTED);
}

/* Экранирование HTML. Telegram в режиме parse_mode=HTML воспримет символы
 * & < > как разметку и вернёт ошибку разбора. В нашей рампе их нет, но если
 * ты потом добавишь < или > для контуров - без этой функции бот сломается.   */
String htmlEscape(const String &src) {
  String out;
  out.reserve(src.length() + 16);
  for (size_t i = 0; i < src.length(); i++) {
    char c = src[i];
    if      (c == '&') out += "&amp;";
    else if (c == '<') out += "&lt;";
    else if (c == '>') out += "&gt;";
    else               out += c;
  }
  return out;
}

/* Кодирование для тела HTTP-запроса. Обязательно: в рампе есть % и +,
 * без кодирования % ломает запрос, а + превращается в пробел.                */
String urlEncode(const String &src) {
  const char *hex = "0123456789ABCDEF";
  String out;
  out.reserve(src.length() * 3);
  for (size_t i = 0; i < src.length(); i++) {
    char c = src[i];
    bool safe = (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z') ||
                (c >= '0' && c <= '9') ||
                c == '-' || c == '_' || c == '.' || c == '~';
    if (safe) out += c;
    else { out += '%'; out += hex[(c >> 4) & 0x0F]; out += hex[c & 0x0F]; }
  }
  return out;
}

bool sendToTelegram(const char *art) {
  if (WiFi.status() != WL_CONNECTED) {
    lastHttpCode = -1;
    return false;
  }

  /* <pre> обязателен: обычный текст Telegram рисует пропорциональным шрифтом,
   * и любая псевдографика в нём превращается в кашу.                         */
  String text = "<pre>" + htmlEscape(String(art)) + "</pre>";
  String body = "chat_id=" + String(TG_CHAT_ID) +
                "&parse_mode=HTML" +
                "&text=" + urlEncode(text);

  /* Адрес и вид соединения зависят от того, идём мы напрямую или через VPS.
   * Сам запрос дальше одинаковый: Bot API на той стороне тот же самый.     */
#if TG_VIA_PROXY
  WiFiClient client;                 // обычный HTTP, шифрует уже сервер
  String url = String("http://") + TG_PROXY_HOST + ":" + String(TG_PROXY_PORT) +
               "/bot" + TG_BOT_TOKEN + "/sendMessage";
#else
  WiFiClientSecure client;
  client.setInsecure();   // не проверяем сертификат: хранить и обновлять
                          // корневой сертификат на плате смысла нет
  String url = String("https://api.telegram.org/bot") + TG_BOT_TOKEN + "/sendMessage";
#endif

  HTTPClient https;
  if (!https.begin(client, url)) {
    lastHttpCode = -2;
    return false;
  }
  https.addHeader("Content-Type", "application/x-www-form-urlencoded");

  lastHttpCode = https.POST(body);
  String reply = https.getString();
  https.end();

  Serial.printf("Telegram HTTP %d: %s\n", lastHttpCode, reply.c_str());
  // 401 = неверный токен, 400 = неверный chat_id или сломана разметка
  return (lastHttpCode == 200);
}


/* =============================================================================
 *  БЛОК 9б. СВОЙ ВЕБ-СЕРВЕР: показ арта без всякого интернета
 * -----------------------------------------------------------------------------
 *  Зачем: Bot API Telegram доступен не везде, а демонстрация не должна
 *  зависеть от того, пускает сеть или нет. Плата поднимает собственную
 *  точку доступа, телефон подключается к ней напрямую - и видит картинку.
 *
 *  Три адреса:
 *    /       - страница целиком
 *    /art    - живой арт с камеры, обычный текст (страница дёргает его сама)
 *    /photo  - арт последнего снимка, сделанного кнопкой
 *
 *  Страница держится в PROGMEM, чтобы не занимать оперативную память.
 * ========================================================================== */
WebServer webServer(WEB_PORT);

static const char PAGE_HTML[] PROGMEM = R"rawliteral(
<!doctype html><html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ESP32-CAM</title>
<style>
  body{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif;
       display:flex;flex-direction:column;align-items:center;gap:14px;padding:16px}
  h2{margin:0;font-size:15px;font-weight:600;color:#8a8a8a;letter-spacing:.08em;
     text-transform:uppercase}
  pre{margin:0;background:#000;color:#0f0;border:1px solid #2a2a2a;border-radius:8px;
      padding:12px;font-family:"Courier New",monospace;font-weight:700;
      line-height:1.0;letter-spacing:0;white-space:pre;
      font-size:clamp(7px,2.6vw,15px)}
  .info{font-size:12px;color:#666}
</style></head><body>
  <h2>Живая картинка</h2>
  <pre id="live">загрузка...</pre>
  <h2>Последний снимок</h2>
  <pre id="shot">нажми кнопку на плате</pre>
  <div class="info" id="info"></div>
<script>
  // Тянем текст по очереди, а не параллельно: у платы один поток,
  // и два одновременных запроса она обслужить не успевает.
  async function tick(){
    try{
      document.getElementById('live').textContent = await (await fetch('/art')).text();
      document.getElementById('shot').textContent = await (await fetch('/photo')).text();
      document.getElementById('info').textContent = 'обновлено ' +
        new Date().toLocaleTimeString();
    }catch(e){
      document.getElementById('info').textContent = 'нет связи с платой';
    }
    setTimeout(tick, 400);
  }
  tick();
</script></body></html>
)rawliteral";

void handleRoot()  { webServer.send_P(200, "text/html; charset=utf-8", PAGE_HTML); }

/* Живой арт: отдаём то, что посчитал последний проход превью. */
void handleArt()   { webServer.send(200, "text/plain; charset=utf-8", asciiArt); }

/* Арт последнего снимка по кнопке. */
void handlePhoto() {
  if (photoCounter == 0) {
    webServer.send(200, "text/plain; charset=utf-8", "нажми кнопку на плате");
  } else {
    webServer.send(200, "text/plain; charset=utf-8", lastPhotoArt);
  }
}

void initWebServer() {
  /* AP_STA: одновременно и своя точка доступа, и подключение к роутеру.
   * Своя точка нужна для показа, подключение к роутеру - для Telegram.  */
  WiFi.mode(WIFI_AP_STA);
  WiFi.softAP(AP_SSID, AP_PASS);

  Serial.print("Точка доступа \"" AP_SSID "\", адрес http://");
  Serial.println(WiFi.softAPIP());

  webServer.on("/",      handleRoot);
  webServer.on("/art",   handleArt);
  webServer.on("/photo", handlePhoto);
  webServer.begin();
}


/* =============================================================================
 *  БЛОК 10. ДВА РЕЖИМА РАБОТЫ: живое превью и снимок
 * ========================================================================== */

/* Один кадр живого превью на дисплей. */
void showLivePreview() {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) return;

  frameToOledGray(fb, grayForOled);
  ditherAtkinson(grayForOled, oledBitmap);

  // Второй аргумент: показывать ли предупреждение об отсутствии сети
  drawOledBitmap(oledBitmap, WiFi.status() != WL_CONNECTED);

  /* Из того же кадра сразу делаем псевдографику для веб-страницы.
   * Считать заново по запросу браузера нельзя: пока идёт HTTP-ответ,
   * трогать камеру из другого места небезопасно.                       */
  frameToAscii(fb, asciiArt);

  esp_camera_fb_return(fb);   // ОБЯЗАТЕЛЬНО возвращать буфер, иначе через
                              // несколько кадров камера просто встанет
}

/* Полный цикл по нажатию кнопки. */
void takeAndSendPhoto() {
  Serial.println("--- Снимок ---");

  /* Вспышки больше нет, поэтому и кадры "на выброс" не нужны: экспозиция
   * камеры не меняется, живой просмотр крутится непрерывно, и в буфере
   * и так лежит свежий кадр с уже устоявшимися настройками.                 */
  camera_fb_t *fb = esp_camera_fb_get();

  if (!fb) {
    showStatus("CAM FAIL");
    delay(1500);
    return;
  }

  // 1) Показываем снимок на дисплее (без индикатора сети - он бы мигал поверх)
  frameToOledGray(fb, grayForOled);
  ditherAtkinson(grayForOled, oledBitmap);
  drawOledBitmap(oledBitmap, false);

  // 2) Делаем из того же кадра псевдографику
  frameToAscii(fb, asciiArt);
  esp_camera_fb_return(fb);   // кадр больше не нужен, отпускаем

  /* Копируем в отдельный буфер: asciiArt дальше перезапишется первым же
   * кадром живого превью, а снимок должен остаться на странице.        */
  strncpy(lastPhotoArt, asciiArt, ART_BUF_LEN - 1);
  lastPhotoArt[ART_BUF_LEN - 1] = '\0';
  photoCounter++;

  Serial.println(asciiArt);   // смотреть в мониторе порта моноширинным шрифтом

  delay(PHOTO_HOLD_MS);       // даём разглядеть снимок

  // 3) Отправляем. Превью на это время остановлено: камера и Wi-Fi одновременно -
  //    это лишняя нагрузка на питание и память.

  /* Сначала убеждаемся, что сеть на месте: роутер мог перезагрузиться, плату
   * могли унести за пределы покрытия. Ждём до WIFI_RETRY_TIMEOUT_MS.         */
  if (!ensureWiFi(WIFI_RETRY_TIMEOUT_MS)) {
    showStatus("NO WIFI");
    delay(2000);
    return;   // арт не отправлен. Дождись, пока маркер сети погаснет,
              // и нажми кнопку ещё раз
  }

  showStatus("Sending...");
  bool ok = sendToTelegram(asciiArt);

  if (ok) {
    showStatus("SENT OK");
  } else {
    char msg[24];
    snprintf(msg, sizeof(msg), "ERR %d", lastHttpCode);
    showStatus(msg);
  }
  delay(1500);
  // дальше loop() сам вернётся к живому превью
}


/* =============================================================================
 *  БЛОК 11. SETUP
 * -----------------------------------------------------------------------------
 *  Порядок важен: сначала дисплей, чтобы все последующие ошибки было видно
 *  на экране, а не только в мониторе порта.
 * ========================================================================== */
void setup() {
  // Гасим белый светодиод самой первой строкой и больше к нему не
  // возвращаемся. До этого момента GPIO4 ничем не управляется, и светодиод
  // подсвечивается те доли секунды, пока работает встроенный загрузчик.
  // Убрать это свечение полностью нельзя: скетч до тех пор ещё не запущен.
  pinMode(PIN_FLASH, OUTPUT);
  digitalWrite(PIN_FLASH, LOW);

  Serial.begin(115200);
  delay(300);
  Serial.println("\n=== ESP32-CAM ASCII bot ===");

  buildGammaTables();          // таблицы должны быть готовы до первого кадра

  initDisplay();
  showStartupBar();            // белая полоса: питание есть, дисплей отвечает

  showStatus("Camera...");
  if (!initCamera()) {
    showStatus("CAM INIT FAIL");
    while (true) { delay(1000); }   // без камеры делать нечего
  }

  pinMode(PIN_BUTTON, INPUT_PULLUP);

  connectWiFi();
  initWebServer();     // своя точка доступа + страница с артом

  showStatus("Ready");
  delay(500);
}


/* =============================================================================
 *  БЛОК 12. LOOP
 * -----------------------------------------------------------------------------
 *  Логика простая: обычно крутим живое превью, а при нажатии кнопки уходим
 *  в полный цикл "снимок - отправка" и потом возвращаемся.
 *  Плюс на каждом проходе дёргаем фоновый реконнект - он почти всегда
 *  выходит мгновенно и превью не тормозит.
 * ========================================================================== */
void loop() {
  wifiKeepAlive();
  webServer.handleClient();   // обслуживаем браузер, если кто-то смотрит

  if (buttonPressed()) {
    takeAndSendPhoto();
  } else {
    showLivePreview();
  }
}

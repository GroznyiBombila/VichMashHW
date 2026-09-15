/* =============================================================================
 *  ДИАГНОСТИКА ДИСПЛЕЯ ЧЕРЕЗ СВОЮ ВЕБ-СТРАНИЦУ
 * -----------------------------------------------------------------------------
 *  Интернет не нужен вообще. Плата поднимает собственную точку доступа,
 *  ты подключаешься к ней телефоном или ноутбуком и открываешь адрес
 *  http://192.168.4.1 - там весь отчёт.
 *
 *  Что проверяет:
 *    1) шину I2C на пинах 14/13 - как в боевом скетче;
 *    2) ту же шину на ПЕРЕВЁРНУТЫХ пинах 13/14 - ловит перепутанные
 *       местами SDA и SCL, это самая частая ошибка при пайке;
 *    3) состояние кнопки на GPIO2;
 *    4) причину последней перезагрузки - покажет просадку питания.
 *
 *  Кнопка "Пересканировать" на странице повторяет проверку. Можно шевелить
 *  провода и сразу видеть результат, не перепрошивая плату.
 * ========================================================================== */

#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>

/* --- Точка доступа, которую поднимает плата ------------------------------ */
#define AP_SSID       "ESP32-DIAG"
#define AP_PASS       "12345678"      // минимум 8 символов

/* --- Пины (те же, что в боевом скетче) ----------------------------------- */
#define PIN_OLED_SDA  14
#define PIN_OLED_SCL  13
#define PIN_BUTTON     2
#define PIN_FLASH      4

WebServer webServer(80);

String report = "";        // текст отчёта, его и отдаём в браузер


/* =============================================================================
 *  СКАН ШИНЫ I2C
 * -----------------------------------------------------------------------------
 *  На каждый адрес шлём пустую посылку и смотрим, ответил ли кто-нибудь
 *  подтверждением (ACK). Ответил - устройство на шине есть.
 *
 *  Пины передаём параметрами, чтобы прогнать сканирование дважды:
 *  в правильном порядке и в перевёрнутом.
 * ========================================================================== */
int scanBus(int sdaPin, int sclPin, const char *label) {
  Wire.end();                          // отпускаем шину от прошлого прохода
  delay(50);

  /* --- Проверка линий ДО начала сканирования -----------------------------
   * В покое обе линии I2C должны быть подтянуты вверх, то есть читаться
   * как 1. Если какая-то читается как 0 - она замкнута на землю.
   * Сканировать в этом случае НЕЛЬЗЯ: драйвер I2C зависает намертво,
   * и с ним зависает вся плата. Поэтому проверяем и выходим.             */
  pinMode(sdaPin, INPUT_PULLUP);
  pinMode(sclPin, INPUT_PULLUP);
  delay(10);
  int sdaIdle = digitalRead(sdaPin);
  int sclIdle = digitalRead(sclPin);

  report += String(label) + " (SDA=" + sdaPin + ", SCL=" + sclPin + "):\n";
  report += "    уровень покоя: SDA=" + String(sdaIdle) +
            "  SCL=" + String(sclIdle) + "   (норма 1 и 1)\n";

  if (sdaIdle == LOW || sclIdle == LOW) {
    report += "    ЛИНИЯ ПРИЖАТА К ЗЕМЛЕ - сканировать нельзя, зависнет\n";
    return -1;                         // -1 = шина неисправна
  }

  Wire.begin(sdaPin, sclPin);
  Wire.setTimeOut(50);                 // мс на операцию, чтобы не залипнуть
  delay(50);

  int found = 0;

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      found++;
      if (found <= 8) {
        char line[64];
        snprintf(line, sizeof(line), "    адрес 0x%02X%s\n", addr,
                 (addr == 0x3C || addr == 0x3D) ? "   <-- ЭТО ДИСПЛЕЙ" : "");
        report += line;
      }
    }
  }

  if (found == 0) {
    report += "    пусто, никто не ответил\n";
  } else if (found > 8) {
    report += "    ...всего " + String(found) + " адресов\n";
    report += "    СТОЛЬКО НЕ БЫВАЕТ: обрыв или замыкание SDA на землю\n";
  }
  return found;
}


/* =============================================================================
 *  ПРОВЕРКА ОДНОГО ПИНА
 * -----------------------------------------------------------------------------
 *  Пин читается дважды: сначала с внутренней подтяжкой ВВЕРХ, потом ВНИЗ.
 *  Подтяжка слабая (около 45 кОм), поэтому она пересиливает только пустоту.
 *  По паре ответов сразу понятно, что к пину подключено:
 *
 *    вверх=1, вниз=0  - пин свободен, подтяжка пересиливает. Норма для
 *                       линии I2C без дисплея или для отпущенной кнопки.
 *    вверх=0, вниз=0  - пин прижат к ЗЕМЛЕ намертво, подтяжку не пересилить.
 *                       Это замыкание.
 *    вверх=1, вниз=1  - пин прижат к ПЛЮСУ снаружи.
 * ========================================================================== */
void checkPin(int pin, const char *name) {
  pinMode(pin, INPUT_PULLUP);
  delay(5);
  int up = digitalRead(pin);

  pinMode(pin, INPUT_PULLDOWN);
  delay(5);
  int down = digitalRead(pin);

  report += String("  ") + name + "  вверх=" + String(up) +
            " вниз=" + String(down) + "  ";

  if (up == HIGH && down == LOW)       report += "свободен\n";
  else if (up == LOW && down == LOW)   report += "ЗАМКНУТ НА ЗЕМЛЮ\n";
  else if (up == HIGH && down == HIGH) report += "ПРИЖАТ К ПЛЮСУ\n";
  else                                 report += "непонятно, пин неисправен\n";

  pinMode(pin, INPUT);                 // отпускаем, чтобы не мешать дальше
}


/* Полный прогон всех проверок. Результат складывается в report. */
void runDiagnostics() {
  report = "";
  Serial.println("[этап] старт диагностики");

  /* --- Причина последней перезагрузки ------------------------------------
   * Если тут окажется просадка питания - это главная проблема,
   * и всё остальное можно не смотреть.                                    */
  esp_reset_reason_t rr = esp_reset_reason();
  report += "Последний сброс: ";
  switch (rr) {
    case ESP_RST_POWERON:  report += "подача питания - норма\n";            break;
    case ESP_RST_EXT:      report += "кнопкой сброса - норма\n";            break;
    case ESP_RST_SW:       report += "программный - норма\n";               break;
    case ESP_RST_PANIC:    report += "аварийный останов программы\n";       break;
    case ESP_RST_INT_WDT:  report += "сторожевой таймер прерываний\n";      break;
    case ESP_RST_TASK_WDT: report += "сторожевой таймер задачи - зависание\n"; break;
    case ESP_RST_WDT:      report += "сторожевой таймер - было зависание\n"; break;
    case ESP_RST_BROWNOUT: report += "ПРОСАДКА ПИТАНИЯ - не хватает тока\n"; break;
    default:               report += "код " + String((int)rr) + "\n";       break;
  }
  report += "Свободно памяти: " + String((int)ESP.getFreeHeap()) + " байт\n\n";

  /* --- Таблица по каждому пину ------------------------------------------- */
  report += "Состояние пинов:\n";
  checkPin(PIN_OLED_SDA, "IO14 (SDA дисплея)");
  checkPin(PIN_OLED_SCL, "IO13 (SCL дисплея)");
  checkPin(PIN_BUTTON,   "IO2  (кнопка)     ");
  checkPin(PIN_FLASH,    "IO4  (вспышка)    ");
  report += "\n";

  /* --- Шина в правильном порядке ---------------------------------------- */
  Serial.println("[этап] скан шины 14/13");
  int direct = scanBus(PIN_OLED_SDA, PIN_OLED_SCL, "Как в скетче");

  /* --- Шина с перевёрнутыми пинами -------------------------------------- */
  Serial.println("[этап] скан шины 13/14");
  int swapped = scanBus(PIN_OLED_SCL, PIN_OLED_SDA, "Если провода перепутаны");

  /* --- Возвращаем шину в штатное состояние ------------------------------ */
  Wire.end();
  delay(50);
  Wire.begin(PIN_OLED_SDA, PIN_OLED_SCL);

  /* --- Кнопка ------------------------------------------------------------ */
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  delay(5);
  int btn = digitalRead(PIN_BUTTON);
  report += "\nКнопка GPIO2: " + String(btn) +
            (btn == LOW ? "  ЗАЛИПЛА на землю\n" : "  норма, отпущена\n");

  /* --- Проверка перемычки между IO2 и IO4 --------------------------------
   * Вспышку больше НЕ зажигаем нигде: GPIO4 всё время остаётся выходом,
   * прижатым к земле, светодиод не загорается ни на миг.
   *
   * Проверка чисто пассивная, в два замера:
   *   замер 1 - GPIO4 выход, прижат к земле. Читаем GPIO2 с подтяжкой вверх.
   *   замер 2 - GPIO4 отпущен во вход, никуда не тянет. Снова читаем GPIO2.
   * Если в первом замере ноль, а во втором единица - значит GPIO2 прижимал
   * к земле именно GPIO4, то есть между ними перемычка припоем.           */
  Serial.println("[этап] проверка перемычки IO2-IO4");

  pinMode(PIN_FLASH, OUTPUT);
  digitalWrite(PIN_FLASH, LOW);          // выход в нуле, светодиод погашен
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  delay(20);
  int btnFlashLow = digitalRead(PIN_BUTTON);

  pinMode(PIN_FLASH, INPUT);             // отпустили, никуда не тянет
  delay(20);
  int btnFlashFree = digitalRead(PIN_BUTTON);

  pinMode(PIN_FLASH, OUTPUT);            // возвращаем в погашенный выход
  digitalWrite(PIN_FLASH, LOW);

  report += "GPIO2 при прижатом GPIO4: " + String(btnFlashLow) + "\n";
  report += "GPIO2 при отпущенном GPIO4: " + String(btnFlashFree) + "\n";

  if (btnFlashLow == LOW && btnFlashFree == HIGH) {
    report += "IO2 и IO4 СОЕДИНЕНЫ между собой - перемычка припоем\n";
  } else if (btnFlashLow == LOW && btnFlashFree == LOW) {
    report += "GPIO2 сидит на земле сам по себе, GPIO4 ни при чём\n";
    report += "  - смотри кнопку: скорее всего припаяна к двум ножкам\n";
    report += "    одной пары, а они внутри кнопки замкнуты навсегда\n";
  } else {
    report += "IO2 и IO4 не соединены - норма\n";
  }

  /* --- Итоговый вывод человеческим языком -------------------------------- */
  report += "\n===== ВЫВОД =====\n";
  if (direct == -1 && swapped == -1) {
    /* Называем конкретный пин: чинить нужно именно его, а не оба. */
    pinMode(PIN_OLED_SDA, INPUT_PULLUP);
    pinMode(PIN_OLED_SCL, INPUT_PULLUP);
    delay(5);
    bool bad14 = (digitalRead(PIN_OLED_SDA) == LOW);
    bool bad13 = (digitalRead(PIN_OLED_SCL) == LOW);

    report += "Шина мертва: линия прижата к земле, обмен не начинается.\n";
    if (bad14 && bad13) report += "К земле прижаты ОБА пина: IO14 и IO13.\n";
    else if (bad14)     report += "К земле прижат IO14 (SDA). IO13 в порядке.\n";
    else if (bad13)     report += "К земле прижат IO13 (SCL). IO14 в порядке.\n";

    report += "\nЧто делать: отпаяй этот провод от платы и пересканируй.\n";
    report += "  стал 'свободен' - замыкание в проводе или в дисплее\n";
    report += "  остался 'ЗАМКНУТ' - замыкание на самой ESP32-CAM\n";
  } else if (direct > 0 && direct <= 8) {
    report += "Дисплей отвечает на правильных пинах. Пайка в порядке.\n";
    report += "Если экран при этом чёрный - дело в контроллере:\n";
    report += "скорее всего это SH1106, а не SSD1306.\n";
  } else if (swapped > 0 && swapped <= 8) {
    report += "SDA и SCL ПЕРЕПУТАНЫ МЕСТАМИ.\n";
    report += "Поменяй два провода местами: SDA идёт на IO14, SCL на IO13.\n";
  } else if (direct > 8 || swapped > 8) {
    report += "Шина закорочена: SDA замкнута на землю или на SCL.\n";
    report += "Проверь пайку на предмет перемычки припоем.\n";
  } else {
    report += "Дисплей не отвечает ни так, ни так. Проверь по порядку:\n";
    report += "  1. Есть ли 3.3 В на выводе VCC модуля дисплея\n";
    report += "  2. Соединена ли земля дисплея с землёй платы\n";
    report += "  3. Пропаяны ли SDA и SCL - прозвони от ножки до пина\n";
    report += "  4. Не отвалился ли провод внутри изоляции\n";
  }

  Serial.println("[этап] диагностика завершена");
  Serial.println(report);
}


/* =============================================================================
 *  ВЕБ-СТРАНИЦА
 * ========================================================================== */
static const char PAGE_HTML[] PROGMEM = R"rawliteral(
<!doctype html><html lang="ru"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Диагностика ESP32-CAM</title>
<style>
  body{margin:0;background:#111;color:#eee;font-family:system-ui,sans-serif;padding:16px}
  h1{font-size:16px;color:#8a8a8a;letter-spacing:.08em;text-transform:uppercase;margin:0 0 12px}
  pre{background:#000;color:#0f0;border:1px solid #2a2a2a;border-radius:8px;
      padding:12px;font-family:"Courier New",monospace;font-size:13px;
      line-height:1.45;white-space:pre-wrap;overflow-x:auto}
  button{background:#2a2a2a;color:#eee;border:1px solid #444;border-radius:8px;
         padding:10px 18px;font-size:14px;cursor:pointer;margin-top:12px}
  button:active{background:#3a3a3a}
</style></head><body>
  <h1>Диагностика ESP32-CAM</h1>
  <pre id="out">загрузка...</pre>
  <button onclick="rescan()">Пересканировать</button>
<script>
  async function load(){
    document.getElementById('out').textContent = await (await fetch('/report')).text();
  }
  async function rescan(){
    document.getElementById('out').textContent = 'сканирую...';
    await fetch('/rescan');
    load();
  }
  load();
</script></body></html>
)rawliteral";

void handleRoot()   { webServer.send_P(200, "text/html; charset=utf-8", PAGE_HTML); }
void handleReport() { webServer.send(200, "text/plain; charset=utf-8", report); }
void handleRescan() { runDiagnostics(); webServer.send(200, "text/plain", "ok"); }


void setup() {
  /* Вспышку гасим сразу, чтобы не слепила и не ела ток. */
  pinMode(PIN_FLASH, OUTPUT);
  digitalWrite(PIN_FLASH, LOW);
  pinMode(PIN_BUTTON, INPUT_PULLUP);

  Serial.begin(115200);
  delay(500);
  Serial.println("\n\n=== ДИАГНОСТИКА ЧЕРЕЗ ВЕБ-СТРАНИЦУ ===");

  /* Только своя точка доступа. К роутеру не подключаемся: интернет
   * тут не нужен, а лишнее ожидание только замедляет старт.            */
  WiFi.mode(WIFI_AP);

  /* Мощность передатчика убавлена. На полной радиомодуль в пике берёт
   * под 300 мА, и если питания впритык - плата уходит в перезагрузку
   * ровно в момент включения WiFi, до того как сеть успеет появиться.
   * Одного клиента и малой мощности для метра расстояния хватает.       */
  WiFi.setTxPower(WIFI_POWER_11dBm);
  WiFi.softAP(AP_SSID, AP_PASS, 1, 0, 1);   // канал 1, не скрытая, 1 клиент

  Serial.println("Сеть: " AP_SSID "   пароль: " AP_PASS);
  Serial.print("Открой в браузере: http://");
  Serial.println(WiFi.softAPIP());

  Serial.println("[этап] точка доступа поднята");

  /* Сервер запускаем ДО диагностики. Тогда страница откроется даже если
   * какая-то из проверок подвиснет - будет видно, на чём именно.        */
  webServer.on("/",       handleRoot);
  webServer.on("/report", handleReport);
  webServer.on("/rescan", handleRescan);
  webServer.begin();
  Serial.println("[этап] веб-сервер запущен");

  runDiagnostics();
}


void loop() {
  webServer.handleClient();

  /* Нажатие кнопки на плате тоже запускает пересканирование. */
  static bool wasDown = false;
  bool isDown = (digitalRead(PIN_BUTTON) == LOW);

  if (isDown && !wasDown) {
    delay(50);
    if (digitalRead(PIN_BUTTON) == LOW) {
      wasDown = true;
      runDiagnostics();
    }
  }
  if (!isDown) wasDown = false;

  delay(10);
}

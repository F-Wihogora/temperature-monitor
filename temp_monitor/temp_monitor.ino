

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// ── LCD setup ────────────────────────────────────────────────────────────────
// Common I2C addresses: 0x27 or 0x3F  ← change if LCD doesn't light up
LiquidCrystal_I2C lcd(0x27, 16, 2);

// ── Candidate name ───────────────────────────────────────────────────────────
const String CANDIDATE_NAME = "Wihogora Florence";   // 17 chars → will scroll

// ── Sensor pin ───────────────────────────────────────────────────────────────
const int SENSOR_PIN = A0;

// ── Scrolling state ───────────────────────────────────────────────────────────
int  scrollPos     = 0;           // current left-most character index
bool needsScroll   = false;       // true when name > 16 chars
unsigned long lastScroll = 0;
const int SCROLL_DELAY = 400;     // ms between scroll steps

// ── Temperature update interval ───────────────────────────────────────────────
unsigned long lastTempUpdate = 0;
const int TEMP_DELAY = 1000;      // read temperature every 1 s

// ─────────────────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(9600);

  lcd.init();
  lcd.backlight();

  needsScroll = (CANDIDATE_NAME.length() > 16);

  // Show static name if short enough, otherwise start scroll
  lcd.setCursor(0, 0);
  if (!needsScroll) {
    lcd.print(CANDIDATE_NAME);
  }

  lcd.setCursor(0, 1);
  lcd.print("Temp: --.- C");
}

// ─────────────────────────────────────────────────────────────────────────────
float readTemperatureCelsius() {

  int   raw  = analogRead(SENSOR_PIN);
  float volt = raw * (5.0 / 1023.0);
  float tempC = volt * 100.0;        // ← change for TMP36: (volt - 0.5) * 100
  return tempC;
}

// ─────────────────────────────────────────────────────────────────────────────
void updateScroll() {
  if (!needsScroll) return;

  unsigned long now = millis();
  if (now - lastScroll < SCROLL_DELAY) return;
  lastScroll = now;

  // Build a 16-char window from the name (wraps around using padding)
  String padded = CANDIDATE_NAME + "                "; // 16 spaces as separator
  int totalLen  = padded.length();

  String window = "";
  for (int i = 0; i < 16; i++) {
    window += padded[(scrollPos + i) % totalLen];
  }

  lcd.setCursor(0, 0);
  lcd.print(window);

  scrollPos = (scrollPos + 1) % totalLen;
}

// ─────────────────────────────────────────────────────────────────────────────
void updateTemperature() {
  unsigned long now = millis();
  if (now - lastTempUpdate < TEMP_DELAY) return;
  lastTempUpdate = now;

  float tempC = readTemperatureCelsius();

  // ── LCD row 2 ────────────────────────────────────────────────────────────
  lcd.setCursor(0, 1);
  lcd.print("Temp: ");
  lcd.print(tempC, 1);    // one decimal place
  lcd.print(" C  ");      // trailing spaces clear old digits

  // ── Serial → PC ──────────────────────────────────────────────────────────
  // Format:  TEMP:23.5   (PC program parses this prefix)
  Serial.print("TEMP:");
  Serial.println(tempC, 1);
}

// ─────────────────────────────────────────────────────────────────────────────
void loop() {
  updateScroll();
  updateTemperature();
}

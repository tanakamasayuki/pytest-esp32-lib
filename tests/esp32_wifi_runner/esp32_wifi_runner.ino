#include <Arduino.h>
#include <WiFi.h>

namespace
{

  constexpr unsigned long kSerialTimeoutMs = 30000;
  constexpr unsigned long kWifiTimeoutMs = 30000;

  String readLineFromSerial(unsigned long timeout_ms)
  {
    const unsigned long start = millis();
    String value;

    while (millis() - start < timeout_ms)
    {
      while (Serial.available() > 0)
      {
        const char ch = static_cast<char>(Serial.read());
        if (ch == '\r')
        {
          continue;
        }

        if (ch == '\n')
        {
          value.trim();
          return value;
        }

        value += ch;
      }

      delay(10);
    }

    value.trim();
    return value;
  }

  bool connectToWifi(const String &ssid, const String &password)
  {
    WiFi.mode(WIFI_STA);
    WiFi.disconnect(true, true);
    delay(200);

    WiFi.begin(ssid.c_str(), password.c_str());

    Serial.printf("SSID '%s'...\n", ssid.c_str());
    Serial.printf("Password length %u...\n", password.length());

    const unsigned long start = millis();
    while (millis() - start < kWifiTimeoutMs)
    {
      if (WiFi.status() == WL_CONNECTED)
      {
        return true;
      }

      delay(250);
    }

    return false;
  }

} // namespace

void setup()
{
  Serial.begin(115200);
  delay(1000);

  Serial.println("WIFI_RUNNER_READY");
  const String ssid = readLineFromSerial(kSerialTimeoutMs);
  const String password = readLineFromSerial(kSerialTimeoutMs);

  if (ssid.isEmpty())
  {
    Serial.println("WIFI_ERROR missing_ssid");
    return;
  }

  if (!connectToWifi(ssid, password))
  {
    Serial.printf("WIFI_ERROR connect_failed %d\n", static_cast<int>(WiFi.status()));
    return;
  }

  Serial.print("WIFI_OK ");
  Serial.println(WiFi.localIP());
}

void loop()
{
  delay(1000);
}

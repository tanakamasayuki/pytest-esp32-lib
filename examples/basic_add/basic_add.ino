#include <addTest.h>

AddTest addTest;

void setup()
{
  Serial.begin(115200);
  delay(1000);
}

void loop()
{
  const int left = 2;
  const int right = 3;
  const int result = addTest.add(left, right);

  Serial.printf("%d + %d = %d\n", left, right, result);
  delay(5000);
}

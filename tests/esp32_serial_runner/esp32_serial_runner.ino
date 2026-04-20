#include <Arduino.h>
#include <addTest.h>

AddTest add_test;

void print_add_result(const int left, const int right) {
  const int result = add_test.add(left, right);
  Serial.printf("ADD %d %d %d\n", left, right, result);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("SERIAL_RUNNER_START");
  print_add_result(2, 3);
  print_add_result(0, 0);
  print_add_result(2, -3);
  Serial.println("SERIAL_RUNNER_DONE");
}

void loop() {
  delay(1000);
}

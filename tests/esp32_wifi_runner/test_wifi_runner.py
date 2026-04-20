import re


def test_wifi_runner_gets_ip_address(dut, wifi_ssid, wifi_password):
    assert wifi_ssid, "wifi_ssid is required"
    assert wifi_password is not None, "wifi_password is required"

    dut.expect_exact("WIFI_RUNNER_READY")
    dut.expect_exact("WIFI_SSID?")
    dut.write(f"{wifi_ssid}\n")

    dut.expect_exact("WIFI_PASSWORD?")
    dut.write(f"{wifi_password}\n")

    dut.expect(re.compile(rb"WIFI_OK (\d{1,3}\.){3}\d{1,3}"), timeout=60)

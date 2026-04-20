import re


def test_wifi_runner_gets_ip_address(dut, wifi_ssid, wifi_password):
    assert wifi_ssid, "wifi_ssid is required"
    assert wifi_password, "wifi_password is required"

    dut.expect_exact("WIFI_RUNNER_READY")
    dut.write(f"{wifi_ssid}\n{wifi_password}\n")

    match = dut.expect(
        [
            re.compile(rb"WIFI_OK ((\d{1,3}\.){3}\d{1,3})"),
            re.compile(rb"WIFI_ERROR ([^\r\n]+)"),
        ],
        timeout=60,
    )

    if match.re.pattern.startswith(b"WIFI_ERROR"):
        raise AssertionError(f"Wi-Fi connection failed: {match.group(1).decode()}")

def test_serial_runner_outputs_expected_results(dut):
    dut.expect_exact("SERIAL_RUNNER_START")
    dut.expect_exact("ADD 2 3 5")
    dut.expect_exact("ADD 0 0 0")
    dut.expect_exact("ADD 2 -3 -1")
    dut.expect_exact("SERIAL_RUNNER_DONE")

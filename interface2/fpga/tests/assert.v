`define assert_equal(actual, expected, message) \
    if ((actual) !== expected) \
    begin \
        $display("[FAIL:ASSERTION] %m (%s:%0d): %s", `__FILE__, `__LINE__, message); \
        $display("\tTime:     %0t", $time); \
        $display("\tExpected: %x", expected); \
        $display("\tActual:   %x", actual); \
    end

`define assert_high(actual, message) \
    `assert_equal(actual, 1, message)

`define assert_low(actual, message) \
    `assert_equal(actual, 0, message)

#include "compas.h"

int test_function() {
    return 42;
}

NB_MODULE(_test_slicer, m) {
    m.doc() = "Test module for slicer";
    m.def("test_function", &test_function, "A simple test function");
} 
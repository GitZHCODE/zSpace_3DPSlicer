#include "compas.h"

int add(int a, int b) {
    return a + b;
}

NB_MODULE(_primitives, m) {
    m.doc() = "C++ primitives for basic operations using nanobind";

    // Basic arithmetic
    m.def("add", &add, "a"_a, "b"_a, "Add two integers");
}

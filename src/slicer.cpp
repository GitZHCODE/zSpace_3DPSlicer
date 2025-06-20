#include "compas.h"
#include "zSlicer.h"
#include <nanobind/stl/vector.h>
#include <nanobind/eigen/dense.h>

NB_MODULE(_slicer, m) {
    m.doc() = "C++ slicer using Eigen and nanobind";

    nb::class_<zMesh>(m, "zMesh")
        .def(nb::init<>())
        .def("setVertices", &zMesh::setVertices)
        .def("setFaces", &zMesh::setFaces)
        .def("getVertices", &zMesh::getVertices)
        .def("getFaces", &zMesh::getFaces);

    nb::class_<zPlane>(m, "zPlane")
        .def(nb::init<>())
        .def(nb::init<const Eigen::Vector3f&, const Eigen::Vector3f&>())
        .def("setOrigin", &zPlane::setOrigin)
        .def("setNormal", &zPlane::setNormal)
        .def("getOrigin", &zPlane::getOrigin)
        .def("getNormal", &zPlane::getNormal);

    nb::class_<zSlicer>(m, "zSlicer")
        .def(nb::init<>())
        .def("setMesh", &zSlicer::setMesh)
        .def("slice", &zSlicer::slice);
} 
#include "compas.h"
#include <nanobind/nanobind.h>
#include <nanobind/stl/vector.h>
#include <nanobind/stl/string.h>
#include <nanobind/ndarray.h>
#include <cstring>
#include "../external/zspace/zSpace_External_C_API.h"

namespace nb = nanobind;

// Helper function to convert Python list to C array
template<typename T>
std::vector<T> py_list_to_vector(nb::list lst) {
    std::vector<T> result;
    for (auto item : lst) {
        result.push_back(nb::cast<T>(item));
    }
    return result;
}

// Helper function to convert C array to Python list
template<typename T>
nb::list vector_to_py_list(const T* arr, size_t size) {
    nb::list result;
    for (size_t i = 0; i < size; ++i) {
        result.append(arr[i]);
    }
    return result;
}

// Graph class wrapper
class Graph {
private:
    zExtGraphHandle handle;

public:
    Graph() : handle(zext_graph_create()) {}
    ~Graph() { if (handle) zext_graph_destroy(handle); }

    void set_handle(zExtGraphHandle new_handle) { handle = new_handle; }

    bool is_valid() const { return zext_graph_is_valid(handle) == 1; }
    int get_vertex_count() const { return zext_graph_get_vertex_count(handle); }
    int get_edge_count() const { return zext_graph_get_edge_count(handle); }

    bool create_graph(const nb::ndarray<double>& vertex_positions,
                     const nb::ndarray<int>& edge_connections) {
        return zext_graph_create_graph(handle,
                                     vertex_positions.data(),
                                     static_cast<int>(vertex_positions.size() / 3),
                                     edge_connections.data(),
                                     static_cast<int>(edge_connections.size() / 2)) == 1;
    }

    nb::tuple get_graph_data() {
        int vertex_count = 0;
        int edge_connections_size = 0;
        
        // First call: get the counts
        if (zext_graph_get_graph_data(handle, true,
                                    nullptr, &vertex_count,
                                    nullptr, &edge_connections_size) != 1) {
            return nb::make_tuple(
                nb::ndarray<double>(nullptr, {0, 3}),
                nb::ndarray<int>(nullptr, {0, 2})
            );
        }
        
        if (vertex_count <= 0 || edge_connections_size <= 0) {
            return nb::make_tuple(
                nb::ndarray<double>(nullptr, {0, 3}),
                nb::ndarray<int>(nullptr, {0, 2})
            );
        }
        
        // Allocate vectors with the correct sizes
        std::vector<double> vertex_positions(vertex_count * 3);
        std::vector<int> edge_connections(edge_connections_size);
        
        // Second call: get the actual data
        if (zext_graph_get_graph_data(handle, false,
                                    vertex_positions.data(), &vertex_count,
                                    edge_connections.data(), &edge_connections_size) == 1) {
            
            // Check if edge indices are reasonable
            bool valid_edges = true;
            for (int i = 0; i < edge_connections_size; ++i) {
                if (edge_connections[i] < 0 || edge_connections[i] >= vertex_count) {
                    valid_edges = false;
                    break;
                }
            }
            
            if (!valid_edges) {
                return nb::make_tuple(
                    nb::ndarray<double>(nullptr, {0, 3}),
                    nb::ndarray<int>(nullptr, {0, 2})
                );
            }
            
            // Allocate memory for the arrays with exact sizes
            double* vertices_data = new double[vertex_count * 3];
            int* edges_data = new int[edge_connections_size];
            
            // Copy data from vectors to allocated memory
            std::memcpy(vertices_data, vertex_positions.data(), 
                       vertex_count * 3 * sizeof(double));
            std::memcpy(edges_data, edge_connections.data(), 
                       edge_connections_size * sizeof(int));
            
            // Create capsules for memory management
            nb::capsule vertices_owner(vertices_data, [](void *p) noexcept {
                delete[] static_cast<double*>(p);
            });
            nb::capsule edges_owner(edges_data, [](void *p) noexcept {
                delete[] static_cast<int*>(p);
            });
            
            // Create numpy arrays with proper ownership using template syntax
            auto vertices_array = nb::ndarray<nb::numpy, double, nb::ndim<2>>(
                vertices_data, 
                {static_cast<size_t>(vertex_count), 3}, 
                vertices_owner
            );
            auto edges_array = nb::ndarray<nb::numpy, int, nb::ndim<1>>(
                edges_data, 
                {static_cast<size_t>(edge_connections_size)}, 
                edges_owner
            );
            
            return nb::make_tuple(vertices_array, edges_array);
        }
        
        return nb::make_tuple(
            nb::ndarray<double>(nullptr, {0, 3}),
            nb::ndarray<int>(nullptr, {0, 2})
        );
    }

    // New methods for graph operations
    bool set_vertex_positions(const nb::ndarray<double>& vertex_positions) {
        return zext_graph_set_vertex_positions(handle,
                                             vertex_positions.data(),
                                             static_cast<int>(vertex_positions.size() / 3)) == 1;
    }

    bool merge_vertices(double tolerance) {
        return zext_graph_merge_vertices(handle, tolerance) == 1;
    }

    nb::tuple separate_graph() {
        std::vector<zExtGraphHandle> components;
        int component_count = 0;
        
        // First call to get count
        if (zext_graph_separate_graph(handle, true,
                                    nullptr, &component_count) == 1) {
            components.resize(component_count);
            // Second call to get actual components
            if (zext_graph_separate_graph(handle, false,
                                        components.data(), &component_count) == 1) {
                // Convert components to Python objects
                nb::list component_list;
                for (int i = 0; i < component_count; ++i) {
                    Graph* graph = new Graph();
                    graph->set_handle(components[i]);
                    component_list.append(graph);
                }
                return nb::make_tuple(component_list, component_count);
            }
        }
        return nb::make_tuple(nb::list(), 0);
    }
};


// Mesh class wrapper
class Mesh {
private:
    zExtMeshHandle handle;

public:
    Mesh() : handle(zext_mesh_create()) {}
    ~Mesh() { if (handle) zext_mesh_destroy(handle); }

    bool is_valid() const { return zext_mesh_is_valid(handle) == 1; }
    int get_vertex_count() const { return zext_mesh_get_vertex_count(handle); }
    int get_face_count() const { return zext_mesh_get_face_count(handle); }

    bool create_mesh(const nb::ndarray<double>& vertex_positions,
                    const nb::ndarray<int>& poly_counts,
                    const nb::ndarray<int>& poly_connections) {
        return zext_mesh_create_mesh(handle,
                                   vertex_positions.data(),
                                   static_cast<int>(vertex_positions.size() / 3),
                                   poly_counts.data(),
                                   static_cast<int>(poly_counts.size()),
                                   poly_connections.data(),
                                   static_cast<int>(poly_connections.size())) == 1;
    }

    nb::tuple get_mesh_data() {
        int vertex_count = get_vertex_count();
        int face_count = get_face_count();
        
        std::vector<double> vertex_positions(vertex_count * 3);
        std::vector<int> poly_counts(face_count);
        std::vector<int> poly_connections;
        
        int poly_connections_size = 0;
        if (zext_mesh_get_mesh_data(handle, false,
                                  vertex_positions.data(), &vertex_count,
                                  poly_counts.data(), &face_count,
                                  nullptr, &poly_connections_size) == 1) {
            poly_connections.resize(poly_connections_size);
            zext_mesh_get_mesh_data(handle, false,
                                  vertex_positions.data(), &vertex_count,
                                  poly_counts.data(), &face_count,
                                  poly_connections.data(), &poly_connections_size);
        }
        
        // Allocate memory for the arrays
        double* vertices_data = new double[vertex_count * 3];
        int* poly_counts_data = new int[face_count];
        int* poly_connections_data = new int[poly_connections_size];
        
        // Copy data from vectors to allocated memory
        std::memcpy(vertices_data, vertex_positions.data(), 
                   vertex_count * 3 * sizeof(double));
        std::memcpy(poly_counts_data, poly_counts.data(), 
                   face_count * sizeof(int));
        std::memcpy(poly_connections_data, poly_connections.data(), 
                   poly_connections_size * sizeof(int));
        
        // Create capsules for memory management
        nb::capsule vertices_owner(vertices_data, [](void *p) noexcept {
            delete[] static_cast<double*>(p);
        });
        nb::capsule poly_counts_owner(poly_counts_data, [](void *p) noexcept {
            delete[] static_cast<int*>(p);
        });
        nb::capsule poly_connections_owner(poly_connections_data, [](void *p) noexcept {
            delete[] static_cast<int*>(p);
        });
        
        // Create numpy arrays with proper ownership using template syntax
        auto vertices_array = nb::ndarray<nb::numpy, double, nb::ndim<2>>(
            vertices_data, 
            {static_cast<size_t>(vertex_count), 3}, 
            vertices_owner
        );
        auto poly_counts_array = nb::ndarray<nb::numpy, int, nb::ndim<1>>(
            poly_counts_data, 
            {static_cast<size_t>(face_count)}, 
            poly_counts_owner
        );
        auto poly_connections_array = nb::ndarray<nb::numpy, int, nb::ndim<1>>(
            poly_connections_data, 
            {static_cast<size_t>(poly_connections_size)}, 
            poly_connections_owner
        );
        
        return nb::make_tuple(vertices_array, poly_counts_array, poly_connections_array);
    }

    bool compute_geodesic_heat(const nb::ndarray<int>& source_vertex_ids,
                             bool normalised,
                             nb::ndarray<float>& out_geodesic_scalars) {
        return zext_mesh_compute_geodesic_heat(handle,
                                             source_vertex_ids.data(),
                                             static_cast<int>(source_vertex_ids.size()),
                                             normalised,
                                             out_geodesic_scalars.data()) == 1;
    }

    // New methods for geodesic computations
    bool compute_geodesic_heat_interpolated(const nb::ndarray<int>& start_vertex_ids,
                                          const nb::ndarray<int>& end_vertex_ids,
                                          float weight,
                                          nb::ndarray<float>& out_geodesic_scalars) {
        return zext_mesh_compute_geodesic_heat_interpolated(handle,
                                                          start_vertex_ids.data(),
                                                          static_cast<int>(start_vertex_ids.size()),
                                                          end_vertex_ids.data(),
                                                          static_cast<int>(end_vertex_ids.size()),
                                                          weight,
                                                          out_geodesic_scalars.data()) == 1;
    }

    nb::tuple compute_geodesic_contours(const nb::ndarray<int>& source_vertex_ids,
                                      int steps,
                                      float dist) {
        std::vector<zExtGraphHandle> contours;
        int contour_count = 0;
        
        // First call to get count
        if (zext_mesh_compute_geodesic_contours(handle, true,
                                              source_vertex_ids.data(),
                                              static_cast<int>(source_vertex_ids.size()),
                                              steps, dist,
                                              nullptr, &contour_count) == 1) {
            contours.resize(contour_count);
            // Second call to get actual contours
            if (zext_mesh_compute_geodesic_contours(handle, false,
                                                  source_vertex_ids.data(),
                                                  static_cast<int>(source_vertex_ids.size()),
                                                  steps, dist,
                                                  contours.data(), &contour_count) == 1) {
                // Convert contours to Python objects
                nb::list contour_list;
                for (int i = 0; i < contour_count; ++i) {
                    Graph* graph = new Graph();
                    graph->set_handle(contours[i]);
                    contour_list.append(graph);
                }
                return nb::make_tuple(contour_list, contour_count);
            }
        }
        return nb::make_tuple(nb::list(), 0);
    }

    nb::tuple compute_geodesic_contours_interpolated(const nb::ndarray<int>& start_vertex_ids,
                                                   const nb::ndarray<int>& end_vertex_ids,
                                                   int steps,
                                                   float dist) {
        std::vector<zExtGraphHandle> contours;
        int contour_count = 0;
        
        // First call to get count
        if (zext_mesh_compute_geodesic_contours_interpolated(handle, true,
                                                          start_vertex_ids.data(),
                                                          static_cast<int>(start_vertex_ids.size()),
                                                          end_vertex_ids.data(),
                                                          static_cast<int>(end_vertex_ids.size()),
                                                          steps, dist,
                                                          nullptr, &contour_count) == 1) {
            contours.resize(contour_count);
            // Second call to get actual contours
            if (zext_mesh_compute_geodesic_contours_interpolated(handle, false,
                                                              start_vertex_ids.data(),
                                                              static_cast<int>(start_vertex_ids.size()),
                                                              end_vertex_ids.data(),
                                                              static_cast<int>(end_vertex_ids.size()),
                                                              steps, dist,
                                                              contours.data(), &contour_count) == 1) {
                // Convert contours to Python objects
                nb::list contour_list;
                for (int i = 0; i < contour_count; ++i) {
                    Graph* graph = new Graph();
                    graph->set_handle(contours[i]);
                    contour_list.append(graph);
                }
                return nb::make_tuple(contour_list, contour_count);
            }
        }
        return nb::make_tuple(nb::list(), 0);
    }
};

NB_MODULE(_zspace, m) {
    m.doc() = "Python bindings for zSpace API";

    // Error handling functions
    m.def("get_last_error", &zext_get_last_error, "Get the last error message");
    m.def("clear_last_error", &zext_clear_last_error, "Clear the last error message");

    // Mesh class
    nb::class_<Mesh>(m, "Mesh")
        .def(nb::init<>())
        .def("is_valid", &Mesh::is_valid)
        .def("get_vertex_count", &Mesh::get_vertex_count)
        .def("get_face_count", &Mesh::get_face_count)
        .def("create_mesh", &Mesh::create_mesh)
        .def("get_mesh_data", &Mesh::get_mesh_data)
        .def("compute_geodesic_heat", &Mesh::compute_geodesic_heat)
        .def("compute_geodesic_heat_interpolated", &Mesh::compute_geodesic_heat_interpolated)
        .def("compute_geodesic_contours", &Mesh::compute_geodesic_contours)
        .def("compute_geodesic_contours_interpolated", &Mesh::compute_geodesic_contours_interpolated);

    // Graph class
    nb::class_<Graph>(m, "Graph")
        .def(nb::init<>())
        .def("is_valid", &Graph::is_valid)
        .def("get_vertex_count", &Graph::get_vertex_count)
        .def("get_edge_count", &Graph::get_edge_count)
        .def("create_graph", &Graph::create_graph)
        .def("get_graph_data", &Graph::get_graph_data)
        .def("set_vertex_positions", &Graph::set_vertex_positions)
        .def("merge_vertices", &Graph::merge_vertices)
        .def("separate_graph", &Graph::separate_graph);
} 
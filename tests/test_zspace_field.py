#!/usr/bin/env python3
"""
Test script for zSpace Field bindings
"""

import numpy as np
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from z3DPSlicer import zField, zGraph, zMesh

def test_field_basic_operations():
    """Test basic field creation and operations"""
    print("Testing basic field operations...")
    
    # Create a field
    field = zField()
    assert field.is_valid(), "Field should be valid after creation"
    
    # Create a simple field grid (2D field)
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    num_x, num_y = 5, 5
    
    success = field.create_field(min_bb, max_bb, num_x, num_y)
    assert success, "Field creation should succeed"
    
    print(f"Field created with {field.get_vertex_count()} vertices and {field.get_value_count()} values")
    
    # Test field values
    values = np.random.rand(field.get_value_count()).astype(np.float32)
    success = field.set_field_values(values)
    assert success, "Setting field values should succeed"
    
    retrieved_values = field.get_field_values()
    assert len(retrieved_values) == len(values), "Retrieved values should match input"
    print("✓ Basic field operations work")

def test_scalar_generation():
    """Test scalar field generation methods"""
    print("\nTesting scalar generation...")
    
    field = zField()
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    field.create_field(min_bb, max_bb, 10, 10)
    
    # Test circle scalar generation
    centre = np.array([5.0, 5.0, 5.0])
    radius = 3.0
    offset = 0.5
    circle_scalars = field.get_scalars_circle(centre, radius, offset, True)
    assert len(circle_scalars) > 0, "Circle scalars should be generated"
    print(f"✓ Circle scalars generated: {len(circle_scalars)} values")
    
    # Test line scalar generation
    start = np.array([0.0, 0.0, 0.0])
    end = np.array([10.0, 10.0, 10.0])
    line_scalars = field.get_scalars_line(start, end, offset, True)
    assert len(line_scalars) > 0, "Line scalars should be generated"
    print(f"✓ Line scalars generated: {len(line_scalars)} values")

def test_graph_based_scalars():
    """Test graph-based scalar generation"""
    print("\nTesting graph-based scalar generation...")
    
    field = zField()
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    field.create_field(min_bb, max_bb, 10, 10)
    
    # Create a simple graph
    graph = zGraph()
    vertices = np.array([
        [0.0, 0.0, 0.0],
        [10.0, 0.0, 0.0],
        [10.0, 10.0, 0.0],
        [0.0, 10.0, 0.0]
    ], dtype=np.float64).flatten()
    
    edges = np.array([
        [0, 1], [1, 2], [2, 3], [3, 0]  # Square perimeter
    ], dtype=np.int32).flatten()
    
    success = graph.create_graph(vertices, edges)
    assert success, "Graph creation should succeed"
    
    # Test graph edge distance scalars
    edge_scalars = field.get_scalars_graph_edge_distance(graph, 1.0, True)
    assert len(edge_scalars) > 0, "Graph edge distance scalars should be generated"
    print(f"✓ Graph edge distance scalars generated: {len(edge_scalars)} values")
    
    # Test polygon scalars
    polygon_scalars = field.get_scalars_polygon(graph, True)
    assert len(polygon_scalars) > 0, "Polygon scalars should be generated"
    print(f"✓ Polygon scalars generated: {len(polygon_scalars)} values")

def test_boolean_operations():
    """Test boolean operations on scalar fields"""
    print("\nTesting boolean operations...")
    
    field = zField()
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    field.create_field(min_bb, max_bb, 10, 10)
    
    # Create two different scalar fields
    scalars_a = np.random.rand(field.get_value_count()).astype(np.float32)
    scalars_b = np.random.rand(field.get_value_count()).astype(np.float32)
    
    # Test boolean operations
    union_result = field.boolean_union(scalars_a, scalars_b, True)
    assert len(union_result) > 0, "Boolean union should work"
    print(f"✓ Boolean union: {len(union_result)} values")
    
    subtract_result = field.boolean_subtract(scalars_a, scalars_b, True)
    assert len(subtract_result) > 0, "Boolean subtract should work"
    print(f"✓ Boolean subtract: {len(subtract_result)} values")
    
    intersect_result = field.boolean_intersect(scalars_a, scalars_b, True)
    assert len(intersect_result) > 0, "Boolean intersect should work"
    print(f"✓ Boolean intersect: {len(intersect_result)} values")
    
    difference_result = field.boolean_difference(scalars_a, scalars_b, True)
    assert len(difference_result) > 0, "Boolean difference should work"
    print(f"✓ Boolean difference: {len(difference_result)} values")

def test_smooth_operations():
    """Test smooth minimum operations"""
    print("\nTesting smooth operations...")
    
    field = zField()
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    field.create_field(min_bb, max_bb, 10, 10)
    
    # Create two scalar fields
    scalars_a = np.random.rand(field.get_value_count()).astype(np.float32)
    scalars_b = np.random.rand(field.get_value_count()).astype(np.float32)
    
    # Test smooth minimum
    smin_result = field.get_scalars_smin(scalars_a, scalars_b, 0.5, 0)
    assert len(smin_result) > 0, "Smooth minimum should work"
    print(f"✓ Smooth minimum: {len(smin_result)} values")
    
    # Test exponential weighted smooth minimum
    exp_smin_result = field.get_scalars_smin_exponential_weighted(scalars_a, scalars_b, 0.5, 0.8)
    assert len(exp_smin_result) > 0, "Exponential weighted smooth minimum should work"
    print(f"✓ Exponential weighted smooth minimum: {len(exp_smin_result)} values")
    
    # Test multiple smooth minimum
    scalars_c = np.random.rand(field.get_value_count()).astype(np.float32)
    multiple_scalars = [scalars_a, scalars_b, scalars_c]
    multi_smin_result = field.get_scalars_smin_multiple(multiple_scalars, 0.5, 0)
    assert len(multi_smin_result) > 0, "Multiple smooth minimum should work"
    print(f"✓ Multiple smooth minimum: {len(multi_smin_result)} values")

def test_analysis_methods():
    """Test field analysis methods"""
    print("\nTesting analysis methods...")
    
    field = zField()
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    field.create_field(min_bb, max_bb, 10, 10)
    
    # Test bounds
    min_bounds, max_bounds = field.get_bounds()
    assert len(min_bounds) == 3 and len(max_bounds) == 3, "Bounds should be 3D"
    print(f"✓ Bounds: min={min_bounds}, max={max_bounds}")
    
    # Test positions
    positions = field.get_positions()
    assert positions.shape[1] == 3, "Positions should be 3D"
    print(f"✓ Positions: {positions.shape[0]} vertices")
    
    # Test gradients
    gradients = field.get_gradients()
    assert gradients.shape[1] == 3, "Gradients should be 3D"
    print(f"✓ Gradients: {gradients.shape[0]} vectors")
    
    # Test ID lookup
    test_position = np.array([5.0, 5.0, 5.0])
    id_result = field.get_id(test_position)
    print(f"✓ ID lookup at {test_position}: {id_result}")

def test_mesh_generation():
    """Test mesh generation from field"""
    print("\nTesting mesh generation...")
    
    field = zField()
    min_bb = np.array([0.0, 0.0, 0.0])
    max_bb = np.array([10.0, 10.0, 10.0])
    field.create_field(min_bb, max_bb, 10, 10)
    
    # Set some field values
    values = np.random.rand(field.get_value_count()).astype(np.float32)
    field.set_field_values(values)
    
    # Test iso-contour generation
    iso_graph = field.get_iso_contour(0.5)
    if iso_graph is not None:
        print(f"✓ Iso-contour generated: {iso_graph.get_vertex_count()} vertices, {iso_graph.get_edge_count()} edges")
    else:
        print("⚠ No iso-contour generated (this is normal for random data)")
    
    # Test mesh generation
    mesh = field.get_mesh()
    if mesh is not None:
        print(f"✓ Mesh generated: {mesh.get_vertex_count()} vertices, {mesh.get_face_count()} faces")
    else:
        print("⚠ No mesh generated (this is normal for random data)")

def main():
    """Run all field tests"""
    print("=== zSpace Field Bindings Test ===\n")
    
    try:
        test_field_basic_operations()
        test_scalar_generation()
        test_graph_based_scalars()
        test_boolean_operations()
        test_smooth_operations()
        test_analysis_methods()
        test_mesh_generation()
        
        print("\n=== All tests completed successfully! ===")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
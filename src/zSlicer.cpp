#include "zSlicer.h"

zMesh::zMesh() {}
zMesh::~zMesh() {}

void zMesh::setVertices(const Eigen::MatrixXf& v) { vertices = v; }
void zMesh::setFaces(const Eigen::MatrixXi& f) { faces = f; }
Eigen::MatrixXf zMesh::getVertices() const { return vertices; }
Eigen::MatrixXi zMesh::getFaces() const { return faces; }

zPlane::zPlane() : origin(0,0,0), normal(0,0,1) {}
zPlane::zPlane(const Eigen::Vector3f& o, const Eigen::Vector3f& n) : origin(o), normal(n.normalized()) {}
zPlane::~zPlane() {}

void zPlane::setOrigin(const Eigen::Vector3f& o) { origin = o; }
void zPlane::setNormal(const Eigen::Vector3f& n) { normal = n.normalized(); }
Eigen::Vector3f zPlane::getOrigin() const { return origin; }
Eigen::Vector3f zPlane::getNormal() const { return normal; }

zSlicer::zSlicer() {}
zSlicer::~zSlicer() {}

void zSlicer::setMesh(const zMesh& m) { mesh = m; }

std::vector<Eigen::MatrixXf> zSlicer::slice(const zPlane& plane) {
    std::vector<Eigen::MatrixXf> contours;
    std::vector<Eigen::Vector3f> intersectionPoints;
    
    Eigen::MatrixXf vertices = mesh.getVertices();
    Eigen::MatrixXi faces = mesh.getFaces();
    
    for (int i = 0; i < faces.rows(); ++i) {
        Eigen::Vector3f v1 = vertices.row(faces(i, 0));
        Eigen::Vector3f v2 = vertices.row(faces(i, 1));
        Eigen::Vector3f v3 = vertices.row(faces(i, 2));
        
        auto points = intersectTriangle(v1, v2, v3, plane);
        intersectionPoints.insert(intersectionPoints.end(), points.begin(), points.end());
    }
    
    if (intersectionPoints.size() >= 2) {
        Eigen::MatrixXf contour(intersectionPoints.size(), 3);
        for (size_t i = 0; i < intersectionPoints.size(); ++i) {
            contour.row(i) = intersectionPoints[i];
        }
        contours.push_back(contour);
    }
    
    return contours;
}

std::vector<Eigen::Vector3f> zSlicer::intersectTriangle(const Eigen::Vector3f& v1, const Eigen::Vector3f& v2, const Eigen::Vector3f& v3, const zPlane& plane) {
    std::vector<Eigen::Vector3f> intersections;
    
    Eigen::Vector3f normal = plane.getNormal();
    float d = normal.dot(plane.getOrigin());
    
    float d1 = normal.dot(v1) - d;
    float d2 = normal.dot(v2) - d;
    float d3 = normal.dot(v3) - d;
    
    if (d1 * d2 < 0) {
        float t = -d1 / (d2 - d1);
        intersections.push_back(v1 + t * (v2 - v1));
    }
    if (d2 * d3 < 0) {
        float t = -d2 / (d3 - d2);
        intersections.push_back(v2 + t * (v3 - v2));
    }
    if (d3 * d1 < 0) {
        float t = -d3 / (d1 - d3);
        intersections.push_back(v3 + t * (v1 - v3));
    }
    
    return intersections;
}

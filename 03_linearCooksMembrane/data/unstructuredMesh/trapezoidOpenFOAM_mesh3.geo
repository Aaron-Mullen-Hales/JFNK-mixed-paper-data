// Unstructured mesh of Fig 9(a) (mesh 3 of the unstructured sequence), Delaunay triangles.
// Regenerated with gmsh 4.11.1:  gmsh trapezoidOpenFOAM_mesh3.geo -3 -format msh2 -o trapezoid_mesh3.msh
// Field[1].VIn = VOut = 4 (target triangle size [mm]); its z = 0 face matches the published raster edge for edge.
lc = 0.12;
thickness = 5.0;   // could be smaller

// Geometry
Point(1) = {0.0, 0.0, 0.0, lc};
Point(2) = {0.0, 44, 0.0, lc};
Point(3) = {48, 60, 0.0, lc};
Point(4) = {48, 44, 0.0, lc};

Line(1) = {1,2};
Line(2) = {2,3};
Line(3) = {3,4};
Line(4) = {4,1};

Curve Loop(1) = {1,2,3,4};
Plane Surface(1) = {1};

// --- Make the interior less regular ---
Mesh.Algorithm = 5;   // Delaunay instead of default Frontal-Delaunay

// Prevent the boundary point sizes from dominating too much
Mesh.MeshSizeFromPoints = 0;
Mesh.MeshSizeFromCurvature = 0;
Mesh.MeshSizeExtendFromBoundary = 0;

// Smooth spatial variation of target size
//Field[1] = MathEval;
//Field[1].F = "0.10*(1.0 + 0.35*sin(6*x)*cos(5*y))";
Field[1] = Box;
Field[1].VIn = 4;
Field[1].VOut = 4;
Field[1].XMin = 0;
Field[1].XMax = 48;
Field[1].YMin = 0;
Field[1].YMax = 60;
Field[1].Thickness = 1.0;

Background Field = 1;

// 3D
out[] = Extrude {0, 0, thickness} {
    Surface{1};
    Layers{1};
    Recombine; // optional
};

// Physical groups
Physical Volume("fluid") = {out[1]};

Physical Surface("frontAndBack") = {1, out[0]};
Physical Surface("left")   = {out[2]};
Physical Surface("top")    = {out[3]};
Physical Surface("right")  = {out[4]};
Physical Surface("bottom") = {out[5]};

Mesh.MshFileVersion = 2.2;

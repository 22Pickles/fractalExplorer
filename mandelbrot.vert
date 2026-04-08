#version 330 core

// Receive the vertex position data from the Python CPU code.
// 'location = 0' matches the glVertexAttribPointer index defined in main().
// Even though it's a 2D screen, OpenGL expects 3D coordinates (x, y, z).
layout(location = 0) in vec3 aPos;

void main()
{
    // gl_Position is a built-in OpenGL variable that determines where 
    // the vertex will actually be placed on the screen (in clip space).
    //
    // We pass the X and Y coordinates directly from our Python array.
    // We force Z to 0.0 because this is a flat 2D projection.
    // The W component is set to 1.0, which is standard for positional coordinates.
    gl_Position = vec4(aPos.x, aPos.y, 0.0, 1.0);
}
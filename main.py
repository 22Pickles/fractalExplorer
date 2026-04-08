import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
import numpy as np


def load_palette(program):
    """
    Generates a color palette and binds it to a 1D OpenGL texture.
    This creates smooth color gradients based on Bernstein-like polynomials.
    """
    PALETTE_SIZE = 1024
    palette = np.zeros((PALETTE_SIZE, 4), dtype=np.uint8)

    # Generate a smooth gradient loop
    for i in range(PALETTE_SIZE):
        t = i / (PALETTE_SIZE - 1)
        t2 = t * t
        t3 = t2 * t

        # Calculate RGB values using non-linear curves for vibrant gradients
        r = 9 * (1 - t) * t3
        g = 15 * ((1 - t)**2) * t2
        b = 8.5 * ((1 - t)**3) * t

        palette[i] = [
            int(np.clip(r * 255, 0, 255)),
            int(np.clip(g * 255, 0, 255)),
            int(np.clip(b * 255, 0, 255)),
            255  # Alpha channel
        ]

    # Convert the numpy array into an OpenGL texture
    palette_tex = create_palette_texture(palette)

    # Bind the generated texture to texture unit 0
    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_1D, palette_tex)

    # Pass the texture and its size to the active shader program
    glUseProgram(program)
    glUniform1i(glGetUniformLocation(program, "u_palette"), 0)
    glUniform1f(glGetUniformLocation(program, "u_palette_size"), PALETTE_SIZE)


def create_palette_texture(palette_array):
    """
    Helper function: Creates and configures an OpenGL 1D texture from a numpy array.
    """
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_1D, tex_id)

    # Load the texture data into OpenGL memory
    glTexImage1D(
        GL_TEXTURE_1D, 0, GL_RGBA8, palette_array.shape[0],
        0, GL_RGBA, GL_UNSIGNED_BYTE, palette_array
    )

    # Set texture parameters for smooth linear interpolation 
    glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_REPEAT)

    # Unbind texture to avoid accidental modifications
    glBindTexture(GL_TEXTURE_1D, 0)
    return tex_id


def load_shader(shader_file, shader_type):
    """
    Reads, creates, and compiles a single shader (Vertex or Fragment) from a text file.
    Raises a RuntimeError if compilation fails, which helps with debugging.
    """
    with open(shader_file, 'r') as f:
        shader_source = f.read()
    
    shader = glCreateShader(shader_type)
    glShaderSource(shader, shader_source)
    glCompileShader(shader)

    # Check for compilation errors and print the log if it fails
    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    
    return shader


def create_program(vertex_file, fragment_file):
    """
    Links a compiled vertex shader and fragment shader into a complete executable program.
    """
    vertex_shader = load_shader(vertex_file, GL_VERTEX_SHADER)
    fragment_shader = load_shader(fragment_file, GL_FRAGMENT_SHADER)

    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    # Check for linking errors
    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError(glGetProgramInfoLog(program).decode())

    # Individual shaders can be safely deleted after they are linked into the program
    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    
    return program


def main():
    """
    Main loop: Initializes Pygame/OpenGL, handles user input, updates state, and renders frames.
    """
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    
    # Setup Pygame display with an OpenGL context
    pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF | pygame.OPENGLBLIT | pygame.RESIZABLE
    )
    pygame.display.set_caption("PyOpenGL Fractal Viewer")

    clock = pygame.time.Clock()
    
    # Initialize shaders and color palette
    program = create_program("mandelbrot.vert", "mandelbrot.frag")
    load_palette(program)
    glUseProgram(program)
    glClearColor(0.1, 0.1, 0.1, 1.0)
    
    # Define a full-screen quad (two combined triangles) to project the shader onto
    quad_vertices = np.array([
        -1.0, -1.0, 0.0, 
         1.0, -1.0, 0.0, 
         1.0,  1.0, 0.0,
         1.0,  1.0, 0.0, 
        -1.0,  1.0, 0.0,
        -1.0, -1.0, 0.0 
    ], dtype=np.float32)

    # Generate and bind Vertex Array Object (VAO) and Vertex Buffer Object (VBO)
    VAO = glGenVertexArrays(1)
    VBO = glGenBuffers(1)
    
    glBindVertexArray(VAO)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
    
    # Describe the layout of the vertex data (3 floats per position)
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * quad_vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    
    glBindBuffer(GL_ARRAY_BUFFER, 0) 
    glBindVertexArray(0)

    # Initial mathematical properties for the fractal
    center_x = -0.5
    center_y = 0.0
    scale = 1.5
    max_iterations = 20

    # Retrieve memory locations for uniform variables in the shader
    u_center_loc = glGetUniformLocation(program, "u_center")
    u_scale_loc = glGetUniformLocation(program, "u_scale")
    u_max_iter_loc = glGetUniformLocation(program, "u_max_iterations")
    u_resolution_loc = glGetUniformLocation(program, "u_resolution")

    # Send the screen resolution to the shader once
    glUniform2f(u_resolution_loc, float(SCREEN_WIDTH), float(SCREEN_HEIGHT))
    
    path = False
    running = True
    
    # Application Loop
    while running:
        
        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Continuously poll relative mouse movement to prevent cursor drifting
        mouse_rel = pygame.mouse.get_rel()

        # Handle mouse drag (Left Click) for smooth panning
        if pygame.mouse.get_pressed()[0]:
            # Scale panning speed proportionally to the current zoom scale
            center_x -= (mouse_rel[0] / SCREEN_WIDTH) * scale * 2.0
            center_y += (mouse_rel[1] / SCREEN_HEIGHT) * scale * 2.0

        # 2. Keyboard Input Processing
        keys = pygame.key.get_pressed()

        # Toggle automated exploration path
        if keys[pygame.K_w]:
            path = True
        elif keys[pygame.K_q]:
            path = False
        
        if path:
            # Automated zoom targeting a visually interesting coordinate
            center_x = -0.761574
            center_y = -0.0847596
            max_iterations += int(max(1, (max_iterations**1.01) / 400))
            scale -= scale / 100

        # Handle manual panning with arrow keys
        move_x, move_y = 0, 0
        if keys[pygame.K_LEFT]:  move_x -= 1
        if keys[pygame.K_RIGHT]: move_x += 1
        if keys[pygame.K_UP]:    move_y += 1
        if keys[pygame.K_DOWN]:  move_y -= 1

        # Calculate vector magnitude to normalize diagonal movement speeds
        size = (move_x**2 + move_y**2)**0.5
        if size != 0:
            # Normalize vector and apply scale-dependent movement speed
            center_x += (move_x / size) * scale * 0.05
            center_y += (move_y / size) * scale * 0.05

        # Handle zooming controls (z: zoom out, x: zoom in)
        if keys[pygame.K_z]:
            scale += scale / 100
        if keys[pygame.K_x]:
            scale -= scale / 100
            
        # Handle detail/iteration controls (c: increase detail, v: decrease detail)
        if keys[pygame.K_c]:
            max_iterations += int(max(1, (max_iterations**1.01) / 200))
        if keys[pygame.K_v]:
            max_iterations -= int(max(1, (max_iterations**1.01) / 200))
        
        # Clamp iterations to prevent negative values crashing the shader
        max_iterations = max(0, max_iterations)

        # 3. Update Shader Uniforms
        # Pass the updated variables from CPU to GPU
        glUniform2f(u_center_loc, center_x, center_y)
        glUniform1f(u_scale_loc, scale)
        glUniform1i(u_max_iter_loc, max_iterations)

        # 4. Rendering Phase
        glClear(GL_COLOR_BUFFER_BIT)
        
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        pygame.display.flip()
        clock.tick(30) # Limit frame rate to 30 FPS

    # 5. Application Cleanup
    glDeleteProgram(program)
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    pygame.quit()


if __name__ == "__main__":
    main()
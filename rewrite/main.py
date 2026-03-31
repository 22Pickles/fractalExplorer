import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
import numpy as np
from mpmath import mp
import ctypes

# 1. Initialize high precision globally
mp.prec = 1000  # Roughly 300 decimal places. Increase if zooming EXTREMELY deep.

def calculate_reference_orbit(center_x, center_y, max_iter):
    # center_x and center_y are already mpmath objects now
    cx, cy = center_x, center_y
    zx, zy = mp.mpf(0), mp.mpf(0)
    
    orbit = np.zeros((max_iter, 2), dtype=np.float32)
    valid_iters = max_iter
    
    for i in range(max_iter):
        new_zx = zx*zx - zy*zy + cx
        new_zy = 2*zx*zy + cy
        zx, zy = new_zx, new_zy
        
        # Downcast to float32 for the shader (relative math is okay with lower prec)
        orbit[i] = [float(zx), float(zy)]
        
        if zx*zx + zy*zy > 100: # Bailout early if center escapes
            valid_iters = i + 1
            break
            
    return orbit, valid_iters

def load_palette(program):
    PALETTE_SIZE = 1024
    palette = np.zeros((PALETTE_SIZE, 4), dtype=np.uint8)

    for i in range(PALETTE_SIZE):
        t = i / (PALETTE_SIZE - 1)
        t2 = t * t
        t3 = t2 * t

        r = 9*(1-t)*t3
        g = 15*((1-t)**2)*t2
        b = 8.5*((1-t)**3)*t

        palette[i] = [
            int(np.clip(r*255, 0, 255)),
            int(np.clip(g*255, 0, 255)),
            int(np.clip(b*255, 0, 255)),
            255
        ]

    palette_tex = create_palette_texture(palette)

    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_1D, palette_tex)

    glUseProgram(program)
    glUniform1i(glGetUniformLocation(program, "u_palette"), 0)
    glUniform1f(glGetUniformLocation(program, "u_palette_size"), PALETTE_SIZE)

def create_palette_texture(palette_array):
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_1D, tex_id)

    glTexImage1D(GL_TEXTURE_1D, 0, GL_RGBA8, palette_array.shape[0], 0, GL_RGBA, GL_UNSIGNED_BYTE, palette_array)
    glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_WRAP_S, GL_REPEAT)

    glBindTexture(GL_TEXTURE_1D, 0)
    return tex_id

def load_shader(shader_file, shader_type):
    with open(shader_file, 'r') as f:
        shader_source = f.read()
    
    shader = glCreateShader(shader_type)
    glShaderSource(shader, shader_source)
    glCompileShader(shader)

    if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
        raise RuntimeError(glGetShaderInfoLog(shader).decode())
    
    return shader

def create_program(vertex_file, fragment_file):
    vertex_shader = load_shader(vertex_file, GL_VERTEX_SHADER)
    fragment_shader = load_shader(fragment_file, GL_FRAGMENT_SHADER)

    program = glCreateProgram()
    glAttachShader(program, vertex_shader)
    glAttachShader(program, fragment_shader)
    glLinkProgram(program)

    if glGetProgramiv(program, GL_LINK_STATUS) != GL_TRUE:
        raise RuntimeError(glGetProgramInfoLog(program).decode())

    glDeleteShader(vertex_shader)
    glDeleteShader(fragment_shader)
    return program

def main():
    pygame.init()
    SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
    display = pygame.display.set_mode(
        (SCREEN_WIDTH, SCREEN_HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF | pygame.OPENGLBLIT | pygame.RESIZABLE
    )
    pygame.display.set_caption("PyOpenGL Deep Fractal Viewer")

    clock = pygame.time.Clock()
    program = create_program("mandelbrot.vert", "mandelbrot.frag")
    load_palette(program)
    glUseProgram(program)
    glClearColor(0.1, 0.1, 0.1, 1.0)
    
    quad_vertices = np.array([
        -1.0, -1.0, 0.0, 
         1.0, -1.0, 0.0, 
         1.0,  1.0, 0.0,
         1.0,  1.0, 0.0, 
        -1.0,  1.0, 0.0,
        -1.0, -1.0, 0.0 
    ], dtype=np.float32)

    VAO = glGenVertexArrays(1)
    VBO = glGenBuffers(1)
    
    glBindVertexArray(VAO)
    glBindBuffer(GL_ARRAY_BUFFER, VBO)
    glBufferData(GL_ARRAY_BUFFER, quad_vertices.nbytes, quad_vertices, GL_STATIC_DRAW)
    
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 3 * quad_vertices.itemsize, ctypes.c_void_p(0))
    glEnableVertexAttribArray(0)
    
    # 2. Setup Texture Buffer Object (TBO) for the reference orbit
    tbo_tex = glGenTextures(1)
    tbo_buf = glGenBuffers(1)

    # 3. Use mpmath objects for tracking coordinates
    center_x = mp.mpf('-0.5')
    center_y = mp.mpf('0.0')
    scale = mp.mpf('1.5')
    max_iterations = 250
    
    u_scale_loc = glGetUniformLocation(program, "u_scale")
    u_max_iter_loc = glGetUniformLocation(program, "u_max_iterations")
    u_ref_iters_loc = glGetUniformLocation(program, "u_ref_iterations")
    u_resolution_loc = glGetUniformLocation(program, "u_resolution")
    u_ref_loc = glGetUniformLocation(program, "u_ref_orbit")

    running = True
    path = False
    
    while running:
        # Handle Window Resize
        SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()
        glViewport(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        glUniform2f(u_resolution_loc, float(SCREEN_WIDTH), float(SCREEN_HEIGHT))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        mouse_rel = pygame.mouse.get_rel()
        keys = pygame.key.get_pressed()

        # Mouse Panning
        if pygame.mouse.get_pressed()[0]:
            # Scale pan speed smoothly based on current zoom
            pan_speed = scale / mp.mpf('500.0')
            center_x -= mp.mpf(mouse_rel[0]) * pan_speed
            center_y += mp.mpf(mouse_rel[1]) * pan_speed
            

        # Path toggle
        if keys[pygame.K_w]: path = True
        if keys[pygame.K_q]: path = False
        
        if path:
            center_x = mp.mpf('-0.761574')
            center_y = mp.mpf('-0.0847596')
            max_iterations += int(max(1,(max_iterations**1.01)/400))
            scale *= mp.mpf('0.99') # Smooth zoom in

        # Keyboard Panning
        move = [0, 0]
        if keys[pygame.K_LEFT]:  move[0] -= 1
        if keys[pygame.K_RIGHT]: move[0] += 1
        if keys[pygame.K_UP]:    move[1] += 1
        if keys[pygame.K_DOWN]:  move[1] -= 1

        size = (move[0]**2 + move[1]**2)**0.5
        if size != 0:
            pan_speed_kb = scale * mp.mpf('0.05')
            center_x += (mp.mpf(move[0]) / mp.mpf(size)) * pan_speed_kb
            center_y += (mp.mpf(move[1]) / mp.mpf(size)) * pan_speed_kb

        # Zoom & Iterations
        if keys[pygame.K_z]: scale *= mp.mpf('0.98') # Zoom in
        if keys[pygame.K_x]: scale *= mp.mpf('1.02') # Zoom out
        if keys[pygame.K_c]: max_iterations += int(max(1, (max_iterations**1.01)/200))
        if keys[pygame.K_v]: max_iterations -= int(max(1, (max_iterations**1.01)/200))
        max_iterations = max(0, max_iterations)

        # 4. Generate Orbit and upload to TBO
        ref_orbit, valid_iters = calculate_reference_orbit(center_x, center_y, max_iterations)
        
        glBindBuffer(GL_TEXTURE_BUFFER, tbo_buf)
        glBufferData(GL_TEXTURE_BUFFER, ref_orbit.nbytes, ref_orbit, GL_DYNAMIC_DRAW)
        
        glActiveTexture(GL_TEXTURE1) # Unit 0 is palette, Unit 1 is TBO
        glBindTexture(GL_TEXTURE_BUFFER, tbo_tex)
        glTexBuffer(GL_TEXTURE_BUFFER, GL_RG32F, tbo_buf)
        
        # 5. Update Uniforms
        glUniform1f(u_scale_loc, float(scale)) # Float is fine here, it's just screen delta scale
        glUniform1i(u_max_iter_loc, max_iterations)
        glUniform1i(u_ref_iters_loc, valid_iters)
        glUniform1i(u_ref_loc, 1) # Tell shader to read TBO from texture unit 1

        glClear(GL_COLOR_BUFFER_BIT)
        
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        pygame.display.flip()
        clock.tick(30)

    glDeleteProgram(program)
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    glDeleteTextures(1, [tbo_tex])
    glDeleteBuffers(1, [tbo_buf])
    pygame.quit()

if __name__ == "__main__":
    main()
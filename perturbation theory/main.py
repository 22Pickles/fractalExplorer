import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
import numpy as np

import mpmath as mp

mp.mp.dps = 2000


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

    glTexImage1D(
            GL_TEXTURE_1D,
            0,
            GL_RGBA8,
            palette_array.shape[0],
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            palette_array
        )

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
    pygame.display.set_caption("PyOpenGL Fractal Viewer")

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
    
    glBindBuffer(GL_ARRAY_BUFFER, 0) 
    glBindVertexArray(0)


    center_x = -0.5
    center_y = 0.0
    scale = 1.5
    max_iterations = 100
    

    u_center_loc = glGetUniformLocation(program, "u_center")
    u_scale_loc = glGetUniformLocation(program, "u_scale")
    u_max_iter_loc = glGetUniformLocation(program, "u_max_iterations")
    u_resolution_loc = glGetUniformLocation(program, "u_resolution")

  
    glUniform2f(u_resolution_loc, float(SCREEN_WIDTH), float(SCREEN_HEIGHT))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        

        mouse_rel = pygame.mouse.get_rel()

        normalized_coords = (center_x / u_resolution_loc) * 2.0 - 1.0
        c = -(u_center_loc + normalized_coords * u_scale_loc)

        if pygame.mouse.get_pressed()[0]:
            center_x += -mouse_rel[0] / 500 * scale**scale**scale
            center_y +=  mouse_rel[1] / 500 * scale**scale**scale

        

        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            break

        move = [0,0]

        if keys[pygame.K_LEFT]:
            move[0] -= 1
        if keys[pygame.K_RIGHT]:
            move[0] += 1
        if keys[pygame.K_UP]:
            move[1] += 1
        if keys[pygame.K_DOWN]:
            move[1] -= 1

        size = (move[0]**2 + move[1]**2)**0.5
        
        if size != 0:
            center_x += move[0]/(1/scale)*0.05*size
            center_y += move[1]/(1/scale)*0.05*size


        if keys[pygame.K_z]:
            scale += scale/100
        if keys[pygame.K_x]:
            scale -= scale/100
        if keys[pygame.K_c]:
            max_iterations += int(max(1,(max_iterations**1.01)/200))
        if keys[pygame.K_v]:
            max_iterations -= int(max(1, ((max_iterations**1.01))/200))
        if max_iterations < 0:
            max_iterations = 0


        
        glUniform2f(u_center_loc, center_x, center_y)
        glUniform1f(u_scale_loc, scale)
        glUniform1i(u_max_iter_loc, max_iterations)

   
        glClear(GL_COLOR_BUFFER_BIT)
        
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)

        pygame.display.flip()
        clock.tick(30)
        print(clock.get_fps())


    glDeleteProgram(program)
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    pygame.quit()

if __name__ == "__main__":
    main()
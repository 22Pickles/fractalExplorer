import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
import numpy as np


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
    SCREEN_WIDTH, SCREEN_HEIGHT = 1500, 1000
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
    pygame.display.set_caption("PyOpenGL Fractal Viewer")

    program = create_program("mandelbrot.vert", "mandelbrot.frag")
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
    max_iterations = 1000
    

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
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                zoom_factor = 1.2
                if event.button == 4:
                    scale /= zoom_factor
                elif event.button == 5: 
                    scale *= zoom_factor

            if event.type == pygame.KEYDOWN:
                move_amount = scale / 5.0 
                if event.key == pygame.K_LEFT:
                    center_x -= move_amount
                elif event.key == pygame.K_RIGHT:
                    center_x += move_amount
                elif event.key == pygame.K_UP:
                    center_y += move_amount
                elif event.key == pygame.K_DOWN:
                    center_y -= move_amount
            

        
        glUniform2f(u_center_loc, center_x, center_y)
        glUniform1f(u_scale_loc, scale)
        glUniform1i(u_max_iter_loc, max_iterations)

   
        glClear(GL_COLOR_BUFFER_BIT)
        
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
        pygame.display.flip()


    glDeleteProgram(program)
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    pygame.quit()

if __name__ == "__main__":
    main()
import pygame
from OpenGL.GL import *
from OpenGL.GLUT import *
import numpy as np

def load_palette(program):

    PALETTE_SIZE = 1024

    palette = np.zeros((PALETTE_SIZE, 4), dtype=np.uint8)
    for i in range(PALETTE_SIZE):
        t = i / (PALETTE_SIZE - 1)

        r = 0.5 + 0.5*np.sin(2*np.pi*(t))
        g = 0.5 + 0.5*np.sin(2*np.pi*(t ))
        b = 0.5 + 0.5*np.sin(2*np.pi*(t ))

        palette[i] = [int(r*255), int(g*255), int(b*255), 255]


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

    palette_tex = create_palette_texture(palette)

    glActiveTexture(GL_TEXTURE0)
    glBindTexture(GL_TEXTURE_1D, palette_tex)

    glUseProgram(program)
    glUniform1i(glGetUniformLocation(program, "u_palette"), 0)
    glUniform1f(glGetUniformLocation(program, "u_palette_size"), PALETTE_SIZE)

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
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF, pygame.RESIZABLE)
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
            center_x += move[0]/scale*0.005*size
            center_y += move[1]/scale*0.005*size


        if keys[pygame.K_z]:
            scale += scale/100
        if keys[pygame.K_x]:
            scale -= scale/100

        max_iterations = 1000 + int((1/scale)**1.15)
        print(max_iterations)


        
        glUniform2f(u_center_loc, center_x, center_y)
        glUniform1f(u_scale_loc, scale)
        glUniform1i(u_max_iter_loc, max_iterations)

   
        glClear(GL_COLOR_BUFFER_BIT)
        
        glBindVertexArray(VAO)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        
        pygame.display.flip()
        clock.tick(30)


    glDeleteProgram(program)
    glDeleteVertexArrays(1, [VAO])
    glDeleteBuffers(1, [VBO])
    pygame.quit()

if __name__ == "__main__":
    main()
import numpy as np

# You can choose any size you like: 256, 512, 1024, 2048, ...
PALETTE_SIZE = 1024

palette = np.zeros((PALETTE_SIZE, 4), dtype=np.uint8)

for i in range(PALETTE_SIZE):
    t = i / (PALETTE_SIZE - 1)

    # Example: smooth rainbow palette
    palette[i, 0] = int(255 * (0.5 + 0.5 * np.sin(6.28 * t)))
    palette[i, 1] = int(255 * (0.5 + 0.5 * np.sin(6.28 * t * 1.7)))
    palette[i, 2] = int(255 * (0.5 + 0.5 * np.sin(6.28 * t * 2.3)))
    palette[i, 3] = 255

from OpenGL.GL import *

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

# Set shader uniform to texture unit 0
glUniform1i(glGetUniformLocation(shader_program, "u_palette"), 0)
glUniform1f(glGetUniformLocation(shader_program, "u_palette_size"), PALETTE_SIZE)

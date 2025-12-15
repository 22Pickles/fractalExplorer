#version 330 core
out vec4 FragColor;

uniform vec2 u_center;
uniform float u_scale;
uniform int u_max_iterations;
uniform vec2 u_resolution;
uniform sampler1D u_palette;
uniform float u_palette_size;

const float LOG2 = 0.6931471805599453;

vec3 escape(vec2 c)
{

    vec2 z = vec2(0.0);

    vec2 old_z = vec2(0.0);
    int period = 20;
    
    for (int i = 0; i < u_max_iterations; ++i)
    {
        if (dot(z, z) > 16.0)
            return vec3(float(i), z);

        float x = z.x;
        float y = z.y;

        float x2 = x*x;
        float y2 = y*y;

        z = vec2(
            x2 - y2 + c.x,
            //abs(2.0 * x * y) + c.y
            2*x*y+c.y
        );

        if (z.x == old_z.x && z.y == old_z.y) 
        {
            return vec3(0.0, z); 
        }

        if (i % period == 0) 
        {
            old_z = z;
        }
    }
    return vec3(0.0, z);
}

void main()
{
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec2 normalized = (uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0) * 2.0;
    vec2 c = (u_center + normalized * u_scale);

    vec3 result = escape(c);
    float iter = result.x;
    vec2 z = result.yz;

    if (iter == 0.0)
    {
        FragColor = vec4(0,0,0,1);
        return;
    }

    float z2 = dot(z,z);
    float log_zn = 0.5 * log(z2);
    float nu = log(log_zn / LOG2) / LOG2;

    float smoothIter = iter + 1.0 - nu;
    float cycles = 1.0;
    float index = smoothIter * cycles / float(u_max_iterations);
    index = fract(index);

    vec4 color = texture(u_palette, index);
    FragColor = color;

    FragColor = color;
}
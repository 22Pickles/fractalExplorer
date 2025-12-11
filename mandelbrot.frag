#version 330 core

out vec4 FragColor;

uniform vec2 u_center;
uniform float u_scale;
uniform int u_max_iterations;
uniform vec2 u_resolution;


vec3 escape(vec2 c)
{
    vec2 z = vec2(0.0, 0.0);
    int iteration = 0;

    while (true)
    {
        if ((length(z) > 4) || (iteration > u_max_iterations))
        {
            return vec3(float(iteration), z.x, z.y);
        }

        float z_real_temp = z.x * z.x - z.y * z.y + c.x;
        z.y = 2.0 * z.x * z.y + c.y; 
        z.x = z_real_temp; 

        iteration = iteration + 1;
    }

    return vec3(0.0, z.x, z.y);
}

void main()
{
    vec2 normalized_coords = (gl_FragCoord.xy / u_resolution) * 2.0 - 1.0;
    vec2 c = u_center + normalized_coords * u_scale;

    vec3 escape_output = escape(c);

    float iteration_count = escape_output.x;
    vec2 z = escape_output.yz;


    if (iteration_count == 0.0) 
    {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
    else 
    {
        float log_z_len = log(length(z));
        float nu = log(log_z_len / log(2.0)) / log(2.0);
        float color_value = iteration_count + 1.0 - nu; 
        
        float r = 0.5 * sin(0.1 * color_value) + 0.5;
        float g = 0.5 * sin(0.15 * color_value) + 0.5;
        float b = 0.5 * sin(0.2 * color_value) + 0.5;

        FragColor = vec4(r, g, b, 1.0);
    }
}

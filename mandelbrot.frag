#version 330 core
out vec4 FragColor;

uniform vec2 u_center;
uniform float u_scale;
uniform int u_max_iterations;
uniform vec2 u_resolution;
uniform sampler1D u_palette;

const float LOG2 = 0.6931471805599453;


vec4 escape_with_derivatives(vec2 c)
{
    vec2 z = vec2(0.0);
    vec2 dz = vec2(0.0);
    

    float q = (c.x - 0.25) * (c.x - 0.25) + c.y * c.y;
    if (q * (q + (c.x - 0.25)) < 0.25 * c.y * c.y) return vec4(0.0, 0.0, 0.0, 0.0);
    if ((c.x + 1.0) * (c.x + 1.0) + c.y * c.y < 0.0625) return vec4(0.0, 0.0, 0.0, 0.0);


    vec2 old_z = vec2(0.0);
    int period = 20;

    for (int i = 0; i < u_max_iterations; ++i)
    {

        float dot_z = dot(z, z);
        if (dot_z > 10000.0) 
        {

            float z_mag = sqrt(dot_z);
            float dz_mag = length(dz);
            
            if (dz_mag == 0.0) dz_mag = 1.0; 

            float dist = 0.5 * z_mag * log(z_mag) / dz_mag;
            return vec4(float(i), dist, z);
        }

        vec2 next_dz = vec2(
            2.0 * (z.x * dz.x - z.y * dz.y) + 1.0,
            2.0 * (z.x * dz.y + z.y * dz.x)
        );
        dz = next_dz;

        z = vec2(
            z.x * z.x - z.y * z.y + c.x,
            2.0 * z.x * z.y + c.y
        );

        if (z == old_z) return vec4(0.0, 0.0, 0.0, 0.0);
        if (i % period == 0) old_z = z;
    }

    return vec4(0.0, 0.0, z);
}

void main()
{
    vec2 uv = gl_FragCoord.xy / u_resolution;
    vec2 normalized = (uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0) * 2.0;
    
    float pixel_size = u_scale / u_resolution.y;

    vec2 c = u_center + normalized * u_scale;

    vec4 result = escape_with_derivatives(c);
    float iter = result.x;
    float dist = result.y;
    vec2 z = result.zw;

    if (iter == 0.0)
    {
        FragColor = vec4(0, 0, 0, 1);
        return;
    }

    
    float z2 = dot(z, z);
    float nu = log(log(z2) / 2.0) / LOG2; // 2.0 is log(sqrt(bailout)) roughly
    float smoothIter = iter + 1.0 - nu;
    float index = fract(smoothIter * 0.01 + 0.5); // Slow down the cycle
    vec4 baseColor = texture(u_palette, index);

    float edgeFactor = clamp(dist / pixel_size, 0.0, 1.0);
    
    edgeFactor = pow(edgeFactor, 0.25); 

    FragColor = mix(vec4(0.0, 0.0, 0.0, 1.0), baseColor, edgeFactor);
}
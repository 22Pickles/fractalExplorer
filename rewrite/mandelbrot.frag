#version 330 core
out vec4 FragColor;

uniform vec2 u_resolution;
uniform float u_scale;
uniform int u_max_iterations;
uniform int u_ref_iterations;

uniform sampler1D u_palette;

// Texture Buffer to hold infinite reference orbit length securely
uniform samplerBuffer u_ref_orbit;

void main() {
    // 1. Calculate Delta (the offset of this pixel from the center)
    vec2 uv = (gl_FragCoord.xy - 0.5 * u_resolution.xy) / u_resolution.y;
    vec2 delta = uv * u_scale; 
    
    vec2 z_diff = vec2(0.0);
    int iter = 0;
    bool escaped = false;

    // 2. Perturbation Loop
    for (int i = 0; i < u_max_iterations; i++) {
        
        // Ensure we don't fetch beyond the valid reference orbit
        // If the center escaped, we clamp to the last valid step to prevent corruption
        int fetch_idx = min(i, u_ref_iterations - 1);
        vec2 z_ref = texelFetch(u_ref_orbit, fetch_idx).xy;

        // Perturbation Formula: 2 * z_ref * z_diff + z_diff^2 + delta
        vec2 next_z_diff = vec2(
            2.0 * (z_ref.x * z_diff.x - z_ref.y * z_diff.y) + (z_diff.x * z_diff.x - z_diff.y * z_diff.y) + delta.x,
            2.0 * (z_ref.x * z_diff.y + z_ref.y * z_diff.x) + (2.0 * z_diff.x * z_diff.y) + delta.y
        );
        
        z_diff = next_z_diff;
        vec2 z_total = z_ref + z_diff;

        if (dot(z_total, z_total) > 4.0) {
            iter = i;
            escaped = true;
            break;
        }
    }

    // 3. Coloring
    if (!escaped) {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
    } else {
        float f_iter = float(iter) / float(u_max_iterations);
        FragColor = texture(u_palette, f_iter);
    }
}
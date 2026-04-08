#version 330 core

// Output color for the current pixel
out vec4 FragColor;

// Variables passed in from the Python/CPU side
uniform vec2 u_center;          // The (x, y) coordinate we are currently looking at
uniform float u_scale;          // The current zoom level
uniform int u_max_iterations;   // Maximum loops before assuming a point is inside the set
uniform vec2 u_resolution;      // The width and height of the screen in pixels
uniform sampler1D u_palette;    // The 1D color gradient texture

// Precomputed constant for natural log of 2, used in smooth coloring math
const float LOG2 = 0.6931471805599453;

/**
 * Calculates whether a point escapes to infinity, and computes its distance to the 
 * edge of the Mandelbrot set using running derivatives.
 * * Returns: vec4(iteration_count, distance_to_edge, final_z.x, final_z.y)
 */
vec4 escape_with_derivatives(vec2 c)
{
    vec2 z = vec2(0.0);
    vec2 dz = vec2(0.0); // Derivative of z with respect to c
    
    // OPTIMIZATION 1: Cardioid and Period-2 Bulb Check
    // The main body of the Mandelbrot set is a cardioid, and the large circle to its left 
    // is the period-2 bulb. If a point is inside these, it will never escape. 
    // We check this mathematically first to save processing time.
    float q = (c.x - 0.25) * (c.x - 0.25) + c.y * c.y;
    if (q * (q + (c.x - 0.25)) < 0.25 * c.y * c.y) return vec4(0.0, 0.0, 0.0, 0.0); // Inside Cardioid
    if ((c.x + 1.0) * (c.x + 1.0) + c.y * c.y < 0.0625) return vec4(0.0, 0.0, 0.0, 0.0); // Inside Period-2 Bulb

    // OPTIMIZATION 2: Periodicity Checking Variables
    // If 'z' eventually repeats a previous value, it is trapped in a loop and will never escape.
    vec2 old_z = vec2(0.0);
    int period = 20;

    // Main Mandelbrot iteration loop
    for (int i = 0; i < u_max_iterations; ++i)
    {
        float dot_z = dot(z, z); // z.x^2 + z.y^2 (Magnitude squared)
        
        // Escape condition: If magnitude squared > 10000, it tends to infinity
        if (dot_z > 10000.0) 
        {
            float z_mag = sqrt(dot_z);
            float dz_mag = length(dz);
            
            if (dz_mag == 0.0) dz_mag = 1.0; // Prevent division by zero error

            // Distance Estimation Formula: Calculates approximate distance to the fractal boundary
            float dist = 0.5 * z_mag * log(z_mag) / dz_mag;
            return vec4(float(i), dist, z); // Return iteration of escape, distance, and final z
        }

        // Calculate the derivative: dz = 2 * z * dz + 1 (using complex number math)
        vec2 next_dz = vec2(
            2.0 * (z.x * dz.x - z.y * dz.y) + 1.0,
            2.0 * (z.x * dz.y + z.y * dz.x)
        );
        dz = next_dz;

        // Calculate the next z: z = z^2 + c (using complex number math)
        z = vec2(
            z.x * z.x - z.y * z.y + c.x,
            2.0 * z.x * z.y + c.y
        );

        // Periodicity Check: If z equals a previously recorded z, it's trapped inside the set
        if (z == old_z) return vec4(0.0, 0.0, 0.0, 0.0);
        if (i % period == 0) old_z = z; // Store z every 20 iterations to check against later
    }

    // If the loop finishes without escaping, assume it's inside the set
    return vec4(0.0, 0.0, z);
}

void main()
{
    // 1. Coordinate Normalization
    // Convert fragment coordinates (pixels) to normalized coordinates (0.0 to 1.0)
    vec2 uv = gl_FragCoord.xy / u_resolution;
    
    // Adjust for screen aspect ratio so the fractal doesn't stretch, mapping to roughly -1.0 to 1.0
    vec2 normalized = (uv - 0.5) * vec2(u_resolution.x / u_resolution.y, 1.0) * 2.0;
    
    // Calculate how large a single pixel is in the fractal's mathematical space
    float pixel_size = u_scale / u_resolution.y;

    // Apply the user's current camera position (center) and zoom (scale)
    vec2 c = u_center + normalized * u_scale;

    // 2. Perform Fractal Math
    vec4 result = escape_with_derivatives(c);
    float iter = result.x;
    float dist = result.y;
    vec2 z = result.zw;

    // If iteration is 0, the point is inside the set (paint it black)
    if (iter == 0.0)
    {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // 3. Smooth Shading (Continuous Potential)
    // Mandelbrot iterations are integers, causing visible "bands" of color.
    // This math calculates a fractional iteration value to smooth the transitions between bands.
    float z2 = dot(z, z);
    float nu = log(log(z2) / 2.0) / LOG2; 
    float smoothIter = iter + 1.0 - nu;
    
    // Map the smoothed iteration value to a 0.0 - 1.0 index for the texture palette
    float index = fract(smoothIter * 0.01 + 0.5); 
    vec4 baseColor = texture(u_palette, index);

    // 4. Distance Estimation Shading (Edge Highlighting)
    // Calculate an edge factor based on how close the pixel is to the boundary
    float edgeFactor = clamp(dist / pixel_size, 0.0, 1.0);
    
    // Apply a power curve to make the glow/edges more pronounced
    edgeFactor = pow(edgeFactor, 0.25); 

    // Mix the vibrant palette color with black based on proximity to the edge
    FragColor = mix(vec4(0.0, 0.0, 0.0, 1.0), baseColor, edgeFactor);
}
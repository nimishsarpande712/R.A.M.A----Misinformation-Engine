import React, { useEffect, useRef } from 'react';
import { Renderer, Program, Triangle, Color } from 'ogl';

interface ThreadsProps {
  color?: [number, number, number];
  amplitude?: number;
  distance?: number;
  enableMouseInteraction?: boolean;
}


const vertexShader = `
attribute vec2 position;
attribute vec2 uv;
varying vec2 vUv;
void main() {
  vUv = uv;
  gl_Position = vec4(position, 0.0, 1.0);
}
`;

const fragmentShader = `
precision highp float;

uniform float iTime;
uniform vec3 iResolution;
uniform vec3 uColor;
uniform float uAmplitude;
uniform float uDistance;
uniform vec2 uMouse;

#define PI 3.1415926538

const int u_line_count = 40;
const float u_line_width = 7.0;
const float u_line_blur = 10.0;

float Perlin2D(vec2 P) {
    vec2 Pi = floor(P);
    vec4 Pf_Pfmin1 = P.xyxy - vec4(Pi, Pi + 1.0);
    vec4 Pt = vec4(Pi.xy, Pi.xy + 1.0);
    Pt = Pt - floor(Pt * (1.0 / 71.0)) * 71.0;
    Pt += vec2(26.0, 161.0).xyxy;
    Pt *= Pt;
    Pt = Pt.xzxz * Pt.yyww;
    vec4 hash_x = fract(Pt * (1.0 / 951.135664));
    vec4 hash_y = fract(Pt * (1.0 / 642.949883));
    vec4 grad_x = hash_x - 0.49999;
    vec4 grad_y = hash_y - 0.49999;
    vec4 grad_results = inversesqrt(grad_x * grad_x + grad_y * grad_y);
    grad_x *= grad_results;
    grad_y *= grad_results;
    vec4 dot_results = grad_x * Pf_Pfmin1.xzxz + grad_y * Pf_Pfmin1.yyww;
    vec2 blend = Pf_Pfmin1.xy * Pf_Pfmin1.xy * (3.0 - 2.0 * Pf_Pfmin1.xy);
    return mix(mix(dot_results.x, dot_results.z, blend.x), mix(dot_results.y, dot_results.w, blend.x), blend.y);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    uv.y *= iResolution.y / iResolution.x;

    float line_strength = 0.0;
    for (int i = 0; i < u_line_count; i++) {
        float line_pos = float(i) / float(u_line_count);
        float dist = abs(uv.y - line_pos);
        float strength = smoothstep(u_line_width / iResolution.y, 0.0, dist);
        line_strength += strength;
    }

    float colorVal = 1.0 - line_strength;
    fragColor = vec4(uColor * colorVal, colorVal);
}

void main() {
    mainImage(gl_FragColor, gl_FragCoord.xy);
}
`;

const Threads: React.FC<ThreadsProps> = ({
  color = [1, 1, 1],
  amplitude = 1,
  distance = 0,
  enableMouseInteraction = false,
  ...rest
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const animationFrameId = useRef<number>();
  const mousePosition = useRef<[number, number]>([0.5, 0.5]);

  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;

    const renderer = new Renderer({ alpha: true });
    const gl = renderer.gl;
    gl.clearColor(0, 0, 0, 0);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
    container.appendChild(gl.canvas);

    const resizeCanvas = () => {
      renderer.setSize(container.offsetWidth, container.offsetHeight);
      program.uniforms.iResolution.value = new Color(
        gl.canvas.width,
        gl.canvas.height,
        gl.canvas.width / gl.canvas.height
      );
    };

    const geometry = new Triangle(gl);
    const program = new Program(gl, {
      vertex: vertexShader,
      fragment: fragmentShader,
      uniforms: {
        iTime: { value: 0 },
        iResolution: {
          value: new Color(gl.canvas.width, gl.canvas.height, gl.canvas.width / gl.canvas.height),
        },
        uColor: { value: new Color(...color) },
        uAmplitude: { value: amplitude },
        uDistance: { value: distance },
        uMouse: { value: new Float32Array(mousePosition.current) },
      },
    });

    const render = (time: number) => {
      program.uniforms.iTime.value = time * 0.001;
      renderer.render({ scene: geometry });
      animationFrameId.current = requestAnimationFrame(render);
    };

    if (enableMouseInteraction) {
      const handleMouseMove = (event: MouseEvent) => {
        const rect = container.getBoundingClientRect();
        const x = (event.clientX - rect.left) / rect.width;
        const y = (event.clientY - rect.top) / rect.height;
        mousePosition.current = [x, y];
        program.uniforms.uMouse.value = new Float32Array(mousePosition.current);
      };
      window.addEventListener('mousemove', handleMouseMove);
      return () => window.removeEventListener('mousemove', handleMouseMove);
    }

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    animationFrameId.current = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animationFrameId.current!);
      window.removeEventListener('resize', resizeCanvas);
      program.destroy();
      renderer.dispose();
    };
  }, [color, amplitude, distance, enableMouseInteraction]);

  return <div ref={containerRef} {...rest} />;
};

export default Threads;
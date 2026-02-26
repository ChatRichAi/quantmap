'use client';

import { useEffect, useRef, useState } from 'react';
import { useTranslations } from 'next-intl';
import * as d3 from 'd3';
import { type EcosystemNode, type EcosystemLink } from '@/lib/api';
import { getNodeColor, getTrustTierColor, formatNumber } from '@/lib/utils';

interface ForceGraphProps {
  nodes: EcosystemNode[];
  links: EcosystemLink[];
  onNodeClick?: (node: EcosystemNode) => void;
}

export default function ForceGraph({ nodes, links, onNodeClick }: ForceGraphProps) {
  const t = useTranslations('tooltip');
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight,
        });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  useEffect(() => {
    if (!svgRef.current || !nodes.length || !dimensions.width) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const { width, height } = dimensions;
    const g = svg.append('g');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform.toString());
      });

    svg.call(zoom);

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const validLinks = links.filter(
      (l) => nodeMap.has(l.source as string) && nodeMap.has(l.target as string)
    );

    const simulation = d3
      .forceSimulation(nodes as d3.SimulationNodeDatum[])
      .force(
        'link',
        d3
          .forceLink(validLinks)
          .id((d: any) => d.id)
          .distance(100)
      )
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius((d: any) => 15 + (d.generation || 0) * 3 + 10));

    const shouldAnimate = !sessionStorage.getItem('evomap_animated');

    const link = g
      .append('g')
      .selectAll('line')
      .data(validLinks)
      .join('line')
      .attr('class', 'link')
      .attr('stroke', '#475569')
      .attr('stroke-width', (d) => Math.min(1 + (d.shared_count || 0) * 0.5, 4));

    const node = g
      .append('g')
      .selectAll<SVGGElement, EcosystemNode>('g')
      .data(nodes)
      .join('g')
      .attr('class', 'node')
      .call(
        d3
          .drag<SVGGElement, EcosystemNode>()
          .on('start', (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d: any) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d: any) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node
      .append('circle')
      .attr('r', (d) => 15 + d.generation * 3)
      .attr('fill', (d) => getNodeColor(d.score))
      .attr('stroke', (d) => getTrustTierColor(d.trust_tier || 0))
      .attr('stroke-width', 2)
      .style('filter', (d) =>
        d.score > 1.0 ? 'drop-shadow(0 0 10px rgba(16, 185, 129, 0.5))' : null
      );

    node
      .append('text')
      .text((d) => d.name)
      .attr('x', 0)
      .attr('y', (d) => 15 + d.generation * 3 + 18)
      .attr('text-anchor', 'middle')
      .attr('font-size', '11px')
      .attr('fill', '#f8fafc')
      .attr('font-weight', '500');

    node
      .on('mouseover', function (event, d) {
        if (tooltipRef.current) {
          tooltipRef.current.style.opacity = '1';
          tooltipRef.current.innerHTML = `
            <div class="font-semibold text-text-primary mb-2 pb-2 border-b border-border">${d.name}</div>
            <div class="flex justify-between my-1.5 text-text-secondary">
              <span>${t('formula')}:</span>
              <span class="text-text-primary font-medium">${d.formula}</span>
            </div>
            <div class="flex justify-between my-1.5 text-text-secondary">
              <span>${t('sharpe')}:</span>
              <span class="font-medium" style="color: ${d.score > 1.0 ? '#10b981' : '#ef4444'}">${formatNumber(d.score)}</span>
            </div>
            <div class="flex justify-between my-1.5 text-text-secondary">
              <span>${t('generation')}:</span>
              <span class="text-text-primary font-medium">${d.generation}</span>
            </div>
            <div class="flex justify-between my-1.5 text-text-secondary">
              <span>${t('trustTier')}:</span>
              <span class="text-text-primary font-medium">T${d.trust_tier || 0}</span>
            </div>
            <div class="flex justify-between my-1.5 text-text-secondary">
              <span>${t('status')}:</span>
              <span class="text-text-primary font-medium">${d.score > 1.0 ? t('passed') : t('failed')}</span>
            </div>
          `;
          tooltipRef.current.style.left = `${event.pageX + 10}px`;
          tooltipRef.current.style.top = `${event.pageY - 10}px`;
        }
      })
      .on('mouseout', function () {
        if (tooltipRef.current) {
          tooltipRef.current.style.opacity = '0';
        }
      })
      .on('click', function (event, d) {
        onNodeClick?.(d);
      });

    if (shouldAnimate) {
      simulation.alpha(1).restart();
      simulation.on('end', () => {
        sessionStorage.setItem('evomap_animated', 'true');
      });
    } else {
      simulation.alpha(0.01).restart();
    }

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links, dimensions, t, onNodeClick]);

  const resetZoom = () => {
    if (svgRef.current) {
      d3.select(svgRef.current)
        .transition()
        .duration(750)
        .call(d3.zoom<SVGSVGElement, unknown>().transform, d3.zoomIdentity);
    }
  };

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full"
      />
      <div
        ref={tooltipRef}
        className="absolute bg-bg-dark/95 border border-border rounded-xl p-4 text-[13px] pointer-events-none opacity-0 transition-opacity z-50 min-w-[220px] shadow-2xl"
      />
    </div>
  );
}

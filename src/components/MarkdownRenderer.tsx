"use client";

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div className="prose prose-neutral max-w-none markdown-content">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
      components={{
        // Кастомизация элементов
        h1: ({ children, ...props }) => (
          <h1 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4 mt-6 first:mt-0" {...props}>
            {children}
          </h1>
        ),
        h2: ({ children, ...props }) => (
          <h2 className="text-xl font-semibold text-neutral-800 dark:text-neutral-100 mb-3 mt-5 first:mt-0" {...props}>
            {children}
          </h2>
        ),
        h3: ({ children, ...props }) => (
          <h3 className="text-lg font-medium text-neutral-800 dark:text-neutral-100 mb-2 mt-4 first:mt-0" {...props}>
            {children}
          </h3>
        ),
        h4: ({ children, ...props }) => (
          <h4 className="text-base font-medium text-neutral-700 dark:text-neutral-200 mb-2 mt-3 first:mt-0" {...props}>
            {children}
          </h4>
        ),
        p: ({ children, ...props }) => (
          <p className="text-neutral-700 dark:text-neutral-200 mb-3 leading-relaxed" {...props}>
            {children}
          </p>
        ),
        strong: ({ children, ...props }) => (
          <strong className="font-semibold text-neutral-900 dark:text-white" {...props}>
            {children}
          </strong>
        ),
        em: ({ children, ...props }) => (
          <em className="italic text-neutral-700 dark:text-neutral-200" {...props}>
            {children}
          </em>
        ),
        ul: ({ children, ...props }) => (
          <ul className="list-disc list-inside mb-4 space-y-1 text-neutral-700 dark:text-neutral-200" {...props}>
            {children}
          </ul>
        ),
        ol: ({ children, ...props }) => (
          <ol className="list-decimal list-inside mb-4 space-y-1 text-neutral-700 dark:text-neutral-200" {...props}>
            {children}
          </ol>
        ),
        li: ({ children, ...props }) => (
          <li className="text-neutral-700 dark:text-neutral-200" {...props}>
            {children}
          </li>
        ),
        blockquote: ({ children, ...props }) => (
          <blockquote className="border-l-4 border-neutral-300 dark:border-neutral-600 pl-4 py-2 my-4 bg-neutral-50 dark:bg-neutral-700 italic text-neutral-600 dark:text-neutral-300" {...props}>
            {children}
          </blockquote>
        ),
        code: ({ children, className, ...props }) => {
          // Не рендерим пустые code блоки
          if (!children || (typeof children === 'string' && !children.trim())) {
            return null;
          }
          
          const isInline = !className;
          if (isInline) {
            return (
              <code className="bg-neutral-100 dark:bg-neutral-700 text-neutral-800 dark:text-neutral-200 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                {children}
              </code>
            );
          }
          return (
            <code className={className} {...props}>
              {children}
            </code>
          );
        },
        pre: ({ children, ...props }) => {
          // Не рендерим пустые pre блоки
          if (!children || (typeof children === 'string' && !children.trim())) {
            return null;
          }
          return (
            <pre className="bg-neutral-900 text-neutral-100 p-4 rounded-lg overflow-x-auto my-4 text-sm" {...props}>
              {children}
            </pre>
          );
        },
        a: ({ children, href, ...props }) => (
          <a 
            href={href} 
            className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline" 
            target="_blank" 
            rel="noopener noreferrer" 
            {...props}
          >
            {children}
          </a>
        ),
        table: ({ children, ...props }) => (
          <div className="overflow-x-auto my-4">
            <table className="min-w-full border-collapse border border-neutral-300 dark:border-neutral-600" {...props}>
              {children}
            </table>
          </div>
        ),
        thead: ({ children, ...props }) => (
          <thead className="bg-neutral-50 dark:bg-neutral-700" {...props}>
            {children}
          </thead>
        ),
        th: ({ children, ...props }) => (
          <th className="border border-neutral-300 dark:border-neutral-600 px-3 py-2 text-left font-semibold text-neutral-900 dark:text-white" {...props}>
            {children}
          </th>
        ),
        td: ({ children, ...props }) => (
          <td className="border border-neutral-300 dark:border-neutral-600 px-3 py-2 text-neutral-700 dark:text-neutral-200" {...props}>
            {children}
          </td>
        ),
        hr: ({ ...props }) => (
          <hr className="border-neutral-300 dark:border-neutral-600 my-6" {...props} />
        ),
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  );
}

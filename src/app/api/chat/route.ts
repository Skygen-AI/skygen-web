import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenAI } from '@google/genai';

// Initialize Gemini AI with server environment variable
const ai = new GoogleGenAI({
  apiKey: process.env.GEMINI_API || ''
});

// System prompt with planning tool instructions
const SYSTEM_PROMPT = `You are a helpful AI assistant. You have access to a planning tool that allows you to create interactive plans.

PLANNING TOOL:

USE the planning tool when the user:
- Asks to create a work, project, or study plan
- Wants to break down a large task into stages
- Plans development, research, or learning
- Discusses a multi-step process
- Asks to create a roadmap, timeline, strategy
- Wants to structure complex activities

SYNTAX:
\`\`\`
[[tool: plan]]
{
  "tasks": [
    {
      "id": "1",
      "title": "Task Title",
      "description": "Detailed description",
      "status": "pending",
      "priority": "high",
      "level": 0,
      "dependencies": [],
      "subtasks": [
        {
          "id": "1.1",
          "title": "Subtask",
          "description": "Subtask description",
          "status": "pending",
          "priority": "medium",
          "tools": ["tool1", "tool2"]
        }
      ]
    }
  ]
}
[[/tool: plan]]
\`\`\`

RULES:
1. Always give a text response BEFORE the tool
2. The tool appears automatically - don't mention it in the text
3. Use proper JSON format
4. IDs should be strings ("1", "1.1")

STATUSES (MUST use different ones):
- "pending" (gray circle) - task not yet started
- "in-progress" (blue dashed) - task currently being executed
- "completed" (green checkmark) - task finished
- "need-help" (yellow triangle) - needs help/blocked
- "failed" (red cross) - task failed/cancelled

PRIORITIES: "high", "medium", "low"

MANDATORY VARIETY:
- In each plan use at least 3-4 different statuses
- Don't make all tasks "pending"
- Show real progress: some tasks "completed", some "in-progress"
- Use "need-help" for complex/blocked tasks
- "failed" for cancelled or failed tasks

Respond in English and use the planning tool for appropriate requests.`;

export async function POST(request: NextRequest) {
  try {
    const { message, history } = await request.json();

    // Check API key availability
    if (!process.env.GEMINI_API) {
      return NextResponse.json(
        { error: 'API key not configured. Check GEMINI_API environment variable.' },
        { status: 500 }
      );
    }

    // Prepare context for Gemini with system prompt
    const contents = [
      {
        role: 'user',
        parts: [{ text: SYSTEM_PROMPT }]
      },
      {
        role: 'model',
        parts: [{ text: 'Understood! I will use the planning tool to create structured plans when appropriate. Ready to help!' }]
      },
      ...history.map((msg: any) => ({
        role: msg.author === 'user' ? 'user' : 'model',
        parts: [{ text: msg.content }]
      })),
      {
        role: 'user',
        parts: [{ text: message }]
      }
    ];

    // Send request to Gemini
    const response = await ai.models.generateContent({
      model: "gemini-2.0-flash-exp",
      contents: contents
    });

    if (!response || !response.text) {
      throw new Error('Empty response from Gemini API');
    }

    return NextResponse.json({ response: response.text });

  } catch (error) {
    console.error('Error calling Gemini API:', error);
    
    let errorMessage = 'An unknown error occurred while calling the AI.';
    
    if (error instanceof Error) {
      if (error.message.includes('API key')) {
        errorMessage = 'Error: API key not configured or invalid.';
      } else if (error.message.includes('quota')) {
        errorMessage = 'Error: API request quota exceeded.';
      } else if (error.message.includes('network')) {
        errorMessage = 'Network error. Check your internet connection.';
      } else {
        errorMessage = `API Error: ${error.message}`;
      }
    }
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    );
  }
}

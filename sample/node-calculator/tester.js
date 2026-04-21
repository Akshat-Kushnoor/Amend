import OpenAI from 'openai';
import readline from "readline";

const openai = new OpenAI({
  apiKey: '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',
  baseURL: 'https://integrate.api.nvidia.com/v1',
})
 
// Create terminal input/output interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});node 

// Store conversation history
let messages = [];

async function chat() {
  rl.question("\nYou: ", async (input) => {
    if (input.toLowerCase() === "exit") {
      console.log("Goodbye 👋");
      rl.close();
      return;
    }

    messages.push({ role: "user", content: input });

    try {
      const completion = await openai.chat.completions.create({
        model: "qwen/qwen3-coder-480b-a35b-instruct",
        messages: messages,
        temperature: 1,
        top_p: 0.95,
        max_tokens: 8192,
        stream: true,
      });

      let assistantReply = "";
      process.stdout.write("AI: ");

      for await (const chunk of completion) {
        const text = chunk.choices[0]?.delta?.content || "";
        process.stdout.write(text);
        assistantReply += text;
      }

      messages.push({ role: "assistant", content: assistantReply });

      chat(); // continue loop
    } catch (err) {
      console.error("\nError:", err.message);
      chat();
    }
  });
}

// Start chat
console.log(" Terminal AI Chat (type 'exit' to quit)");
chat();
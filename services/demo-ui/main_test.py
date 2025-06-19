import gradio as gr
import numpy as np



def on_submit(text, history):
    history.extend([
        gr.ChatMessage(
            role="user",
            content=text["text"]
        ),
        gr.ChatMessage(
            role="user",
            content="Processing your message..."
        )
    ]
    )

    history.append(
        gr.ChatMessage(
            role="assistant",
            content="This is a placeholder response. Replace with actual model inference."
        )
    )

    return {"text": "", "files": []}, history

with gr.Blocks() as demo:
    chatbot = gr.Chatbot(label="Chatterbox", type="messages")
    text_input = gr.MultimodalTextbox(
        label="Type your message here",
        placeholder="Type your message here",
        sources=["microphone"])
    
    text_input.submit(
        on_submit,
        inputs=[text_input, chatbot],
        outputs=[text_input, chatbot]
    )

demo.launch(
    server_name="0.0.0.0",
)
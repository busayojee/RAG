from app.st import setup_page_styling, initialize_session_state, initialize_rag_system, load_session_state, render_sidebar, render_chat_interface, save_session_state



def main():
    setup_page_styling()
    initialize_session_state()
    load_session_state()
    rag = initialize_rag_system()
    render_sidebar(rag)
    render_chat_interface(rag)
    save_session_state()

if __name__ == "__main__":
    main()
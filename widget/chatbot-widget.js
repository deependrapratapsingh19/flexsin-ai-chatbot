(() => {
    "use strict";

    // =========================================================
    // CONFIGURATION
    // =========================================================

    const WIDGET_ID = "flexsin-ai-widget";
    const CSS_ID = "flexsin-ai-widget-css";

    const WIDGET_BASE_URL =
        "http://chat.flexsin.com/widget";

    const CHATBOT_URL =
        "http://chat.flexsin.com/?embed=true";


    // =========================================================
    // PREVENT DUPLICATE WIDGET
    // =========================================================

    const existingWidget =
        document.getElementById(WIDGET_ID);

    if (existingWidget) {
        console.log(
            "Flexsin AI widget already exists."
        );

        return;
    }


    // =========================================================
    // LOAD WIDGET CSS
    // =========================================================

    let stylesheet =
        document.getElementById(CSS_ID);

    if (!stylesheet) {

        stylesheet =
            document.createElement("link");

        stylesheet.id =
            CSS_ID;

        stylesheet.rel =
            "stylesheet";

        stylesheet.href =
            `${WIDGET_BASE_URL}/chatbot-widget.css?v=${Date.now()}`;

        document.head.appendChild(
            stylesheet
        );
    }


    // =========================================================
    // ROOT
    // =========================================================

    const root =
        document.createElement("div");

    root.id =
        WIDGET_ID;


    // =========================================================
    // FLOATING AI BUTTON
    // =========================================================

    const openButton =
        document.createElement("button");

    openButton.id =
        "flexsin-ai-open-button";

    openButton.type =
        "button";

    openButton.textContent =
        "AI";

    openButton.title =
        "Ask Flexsin AI";

    openButton.setAttribute(
        "aria-label",
        "Open Flexsin AI Assistant"
    );

    openButton.setAttribute(
        "aria-expanded",
        "false"
    );


    // =========================================================
    // CHAT WINDOW
    // =========================================================

    const chatWindow =
        document.createElement("section");

    chatWindow.id =
        "flexsin-ai-window";

    chatWindow.setAttribute(
        "aria-hidden",
        "true"
    );

    chatWindow.setAttribute(
        "aria-label",
        "Flexsin AI Assistant"
    );


    // =========================================================
    // HEADER
    // =========================================================

    const header =
        document.createElement("div");

    header.className =
        "flexsin-ai-header";


    // =========================================================
    // HEADER LEFT
    // =========================================================

    const identity =
        document.createElement("div");

    identity.className =
        "flexsin-ai-identity";


    const avatar =
        document.createElement("div");

    avatar.className =
        "flexsin-ai-avatar";

    avatar.textContent =
        "AI";


    const info =
        document.createElement("div");

    info.className =
        "flexsin-ai-info";


    const title =
        document.createElement("strong");

    title.textContent =
        "Flexsin AI Assistant";


    const status =
        document.createElement("span");

    status.className =
        "flexsin-ai-status";


    const statusDot =
        document.createElement("span");

    statusDot.className =
        "flexsin-ai-status-dot";


    const statusText =
        document.createElement("span");

    statusText.textContent =
        "Online";


    status.appendChild(
        statusDot
    );

    status.appendChild(
        statusText
    );


    info.appendChild(
        title
    );

    info.appendChild(
        status
    );


    identity.appendChild(
        avatar
    );

    identity.appendChild(
        info
    );


    // =========================================================
    // HEADER ACTIONS
    // =========================================================

    const actions =
        document.createElement("div");

    actions.className =
        "flexsin-ai-actions";


    // =========================================================
    // REFRESH BUTTON
    // =========================================================

    const refreshButton =
        document.createElement("button");

    refreshButton.type =
        "button";

    refreshButton.className =
        "flexsin-ai-control";

    refreshButton.textContent =
        "↻";

    refreshButton.title =
        "Reload chatbot";

    refreshButton.setAttribute(
        "aria-label",
        "Reload chatbot"
    );


    // =========================================================
    // CLOSE BUTTON
    // =========================================================

    const closeButton =
        document.createElement("button");

    closeButton.type =
        "button";

    closeButton.className =
        "flexsin-ai-control flexsin-ai-close";

    closeButton.textContent =
        "×";

    closeButton.title =
        "Close chatbot";

    closeButton.setAttribute(
        "aria-label",
        "Close chatbot"
    );


    // =========================================================
    // HEADER ASSEMBLY
    // =========================================================

    actions.appendChild(
        refreshButton
    );

    actions.appendChild(
        closeButton
    );


    header.appendChild(
        identity
    );

    header.appendChild(
        actions
    );


    // =========================================================
    // FRAME WRAPPER
    // =========================================================

    const frameWrapper =
        document.createElement("div");

    frameWrapper.className =
        "flexsin-ai-frame-wrapper";


    // =========================================================
    // LOADER
    // =========================================================

    const loader =
        document.createElement("div");

    loader.className =
        "flexsin-ai-loader";


    const spinner =
        document.createElement("div");

    spinner.className =
        "flexsin-ai-spinner";


    const loaderText =
        document.createElement("span");

    loaderText.textContent =
        "Loading AI Assistant...";


    loader.appendChild(
        spinner
    );

    loader.appendChild(
        loaderText
    );


    // =========================================================
    // CHATBOT IFRAME
    // =========================================================

    const chatbotFrame =
        document.createElement("iframe");

    chatbotFrame.id =
        "flexsin-ai-frame";

    chatbotFrame.className =
        "flexsin-ai-frame";

    chatbotFrame.src =
        CHATBOT_URL;

    chatbotFrame.title =
        "Flexsin AI Assistant";

    chatbotFrame.setAttribute(
        "allow",
        "clipboard-read; clipboard-write"
    );


    // =========================================================
    // FRAME ASSEMBLY
    // =========================================================

    frameWrapper.appendChild(
        loader
    );

    frameWrapper.appendChild(
        chatbotFrame
    );


    // =========================================================
    // WINDOW ASSEMBLY
    // =========================================================

    chatWindow.appendChild(
        header
    );

    chatWindow.appendChild(
        frameWrapper
    );


    // =========================================================
    // ROOT ASSEMBLY
    // =========================================================

    root.appendChild(
        openButton
    );

    root.appendChild(
        chatWindow
    );


    // IMPORTANT:
    // Widget gets added before event listeners.
    document.body.appendChild(
        root
    );


    // =========================================================
    // OPEN CHATBOT
    // =========================================================

    function openChatbot() {

        chatWindow.classList.add(
            "open"
        );

        chatWindow.setAttribute(
            "aria-hidden",
            "false"
        );

        openButton.setAttribute(
            "aria-expanded",
            "true"
        );

    }


    // =========================================================
    // CLOSE CHATBOT
    // =========================================================

    function closeChatbot() {

        chatWindow.classList.remove(
            "open"
        );

        chatWindow.setAttribute(
            "aria-hidden",
            "true"
        );

        openButton.setAttribute(
            "aria-expanded",
            "false"
        );

    }


    // =========================================================
    // TOGGLE CHATBOT
    // =========================================================

    function toggleChatbot() {

        const isOpen =
            chatWindow.classList.contains(
                "open"
            );

        if (isOpen) {

            closeChatbot();

        }
        else {

            openChatbot();

        }

    }


    // =========================================================
    // RELOAD CHATBOT
    // =========================================================

    function reloadChatbot() {

        loader.classList.remove(
            "hidden"
        );

        chatbotFrame.src =
            "about:blank";

        window.setTimeout(
            () => {

                chatbotFrame.src =
                    `${CHATBOT_URL}&reload=${Date.now()}`;

            },
            150
        );

    }


    // =========================================================
    // EVENT LISTENERS
    // =========================================================

    openButton.addEventListener(
        "click",
        toggleChatbot
    );


    closeButton.addEventListener(
        "click",
        closeChatbot
    );


    refreshButton.addEventListener(
        "click",
        reloadChatbot
    );


    // =========================================================
    // IFRAME LOAD
    // =========================================================

    chatbotFrame.addEventListener(
        "load",
        () => {

            loader.classList.add(
                "hidden"
            );

        }
    );


    // =========================================================
    // ESC KEY
    // =========================================================

    document.addEventListener(
        "keydown",
        (event) => {

            if (
                event.key === "Escape" &&
                chatWindow.classList.contains(
                    "open"
                )
            ) {

                closeChatbot();

            }

        }
    );


    // =========================================================
    // SUCCESS
    // =========================================================

    console.log(
        "Flexsin AI widget initialized successfully."
    );

    console.log(
        "Widget:",
        root
    );

    console.log(
        "CSS:",
        stylesheet.href
    );

    console.log(
        "Chatbot URL:",
        CHATBOT_URL
    );

})();
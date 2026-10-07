(() => {
    "use strict";

    const LOADER_ID =
        "flexsin-ai-widget-loader";

    const WIDGET_ID =
        "flexsin-ai-widget";


    // Prevent duplicate loading
    if (
        document.getElementById(LOADER_ID) ||
        document.getElementById(WIDGET_ID)
    ) {
        return;
    }


    const script =
        document.createElement("script");


    script.id =
        LOADER_ID;


    script.src =
    "https://flexsin-ai-chatbot-1.onrender.com/chatbot-widget.js";


    script.async =
        true;


    script.onload =
        () => {
            console.log(
                "Flexsin AI widget loaded."
            );
        };


    script.onerror =
        (error) => {
            console.error(
                "Flexsin AI widget failed to load.",
                error
            );
        };


    document.head.appendChild(
        script
    );
})();
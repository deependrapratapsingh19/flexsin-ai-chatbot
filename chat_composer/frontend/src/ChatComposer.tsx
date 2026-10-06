import React, {
  ChangeEvent,
  KeyboardEvent,
  useRef,
  useState
} from "react";


type EncodedFile = {
  name: string;
  type: string;
  size: number;
  data: string;
};


type ComposerAction =
  | "message"
  | "files"
  | "library"
  | "image"
  | "web"
  | "github";


type SubmissionPayload = {
  action: ComposerAction;
  text: string;
  files: EncodedFile[];
};


type Props = {
  placeholder: string;

  disabled: boolean;

  allowedExtensions: string[];

  /*
   * IMPORTANT:
   *
   * Streamlit state defines only one trigger:
   *
   * submission
   *
   * Therefore this cannot be:
   *
   * key: string
   *
   * It must be the literal:
   *
   * name: "submission"
   */
  setTriggerValue: (
    name: "submission",
    value: SubmissionPayload
  ) => void;
};


const ChatComposer: React.FC<Props> = ({
  placeholder,
  disabled,
  allowedExtensions,
  setTriggerValue
}) => {

  // ========================================================
  // TEXT
  // ========================================================

  const [
    text,
    setText
  ] = useState("");


  // ========================================================
  // MENU
  // ========================================================

  const [
    menuOpen,
    setMenuOpen
  ] = useState(false);


  // ========================================================
  // CURRENT ACTION
  // ========================================================

  const [
    selectedAction,
    setSelectedAction
  ] = useState<ComposerAction>(
    "message"
  );


  // ========================================================
  // ATTACHED FILES
  // ========================================================

  const [
    files,
    setFiles
  ] = useState<EncodedFile[]>(
    []
  );


  // ========================================================
  // HIDDEN FILE INPUT
  // ========================================================

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null
    );


  // ========================================================
  // FILE -> BASE64
  // ========================================================

  const fileToBase64 = (
    file: File
  ): Promise<string> => {

    return new Promise(
      (
        resolve,
        reject
      ) => {

        const reader =
          new FileReader();


        reader.onload = () => {

          if (
            typeof reader.result
            === "string"
          ) {

            resolve(
              reader.result
            );

          } else {

            reject(
              new Error(
                "Unable to read file."
              )
            );
          }
        };


        reader.onerror = () => {

          reject(
            reader.error
          );
        };


        reader.readAsDataURL(
          file
        );
      }
    );
  };


  // ========================================================
  // FILE SELECTION
  // ========================================================

  const onFileChanged = async (
    event: ChangeEvent<HTMLInputElement>
  ) => {

    const selectedFiles =
      Array.from(
        event.target.files || []
      );


    if (
      selectedFiles.length === 0
    ) {

      return;
    }


    try {

      const converted:
        EncodedFile[] = [];


      for (
        const file
        of selectedFiles
      ) {

        const data =
          await fileToBase64(
            file
          );


        converted.push(
          {
            name:
              file.name,

            type:
              file.type
              || "application/octet-stream",

            size:
              file.size,

            data:
              data
          }
        );
      }


      setFiles(
        converted
      );


      setSelectedAction(
        "files"
      );


      setMenuOpen(
        false
      );


      /*
       * Reset input so same file can
       * be selected again later.
       */
      event.target.value = "";

    } catch (error) {

      console.error(
        "Unable to read selected files:",
        error
      );
    }
  };


  // ========================================================
  // CHOOSE TOOL
  // ========================================================

  const chooseAction = (
    action: ComposerAction
  ) => {

    setMenuOpen(
      false
    );


    // ======================================================
    // FILES
    //
    // Open browser / Windows file picker
    // ======================================================

    if (
      action === "files"
    ) {

      fileInputRef.current?.click();

      return;
    }


    // ======================================================
    // OTHER TOOLS
    // ======================================================

    setSelectedAction(
      action
    );


    setFiles(
      []
    );
  };


  // ========================================================
  // RESET TOOL
  // ========================================================

  const resetTool = () => {

    setSelectedAction(
      "message"
    );


    setFiles(
      []
    );
  };


  // ========================================================
  // SUBMIT MESSAGE
  // ========================================================

  const submit = () => {

    if (disabled) {
      return;
    }


    const cleanText =
      text.trim();


    /*
     * Normal message cannot be empty.
     *
     * File submission can be sent
     * without text.
     */
    if (
      !cleanText
      && files.length === 0
      && selectedAction === "message"
    ) {

      return;
    }


    const payload:
      SubmissionPayload = {

        action:
          selectedAction,

        text:
          cleanText,

        files:
          files
      };


    // ======================================================
    // SEND EVENT TO STREAMLIT
    // ======================================================

    setTriggerValue(
      "submission",
      payload
    );


    // ======================================================
    // RESET COMPOSER AFTER SEND
    // ======================================================

    setText(
      ""
    );


    setFiles(
      []
    );


    setSelectedAction(
      "message"
    );


    setMenuOpen(
      false
    );
  };


  // ========================================================
  // ENTER = SEND
  //
  // SHIFT + ENTER = NEW LINE
  // ========================================================

  const onKeyDown = (
    event:
      KeyboardEvent<HTMLTextAreaElement>
  ) => {

    if (
      event.key === "Enter"
      && !event.shiftKey
    ) {

      event.preventDefault();

      submit();
    }
  };


  // ========================================================
  // ACTIVE PLACEHOLDER
  // ========================================================

  let activePlaceholder =
    placeholder;


  if (
    selectedAction === "image"
  ) {

    activePlaceholder =
      "Describe the image you want...";
  }


  else if (
    selectedAction === "web"
  ) {

    activePlaceholder =
      "Search the web...";
  }


  else if (
    selectedAction === "github"
  ) {

    activePlaceholder =
      "Enter repository or ask about GitHub...";
  }


  else if (
    selectedAction === "library"
  ) {

    activePlaceholder =
      "Select or search your library...";
  }


  else if (
    selectedAction === "files"
  ) {

    activePlaceholder =
      "Ask something about the attached files...";
  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="composer-wrapper">


      {/* ====================================================
          CHATGPT-STYLE PLUS MENU
      ==================================================== */}

      {
        menuOpen
        && (

          <div className="tools-menu">


            {/* ==============================================
                ADD PHOTOS & FILES
            ============================================== */}

            <button
              type="button"

              onClick={() =>
                chooseAction(
                  "files"
                )
              }
            >

              <span>
                📎
              </span>

              Add photos & files

            </button>


            {/* ==============================================
                LIBRARY
            ============================================== */}

            <button
              type="button"

              onClick={() =>
                chooseAction(
                  "library"
                )
              }
            >

              <span>
                📚
              </span>

              Add from library

            </button>


            {/* ==============================================
                CREATE IMAGE
            ============================================== */}

            <button
              type="button"

              onClick={() =>
                chooseAction(
                  "image"
                )
              }
            >

              <span>
                🎨
              </span>

              Create image

            </button>


            {/* ==============================================
                WEB SEARCH
            ============================================== */}

            <button
              type="button"

              onClick={() =>
                chooseAction(
                  "web"
                )
              }
            >

              <span>
                🌐
              </span>

              Web search

            </button>


            {/* ==============================================
                GITHUB
            ============================================== */}

            <button
              type="button"

              onClick={() =>
                chooseAction(
                  "github"
                )
              }
            >

              <span>
                🐙
              </span>

              GitHub

            </button>


          </div>

        )
      }


      {/* ====================================================
          ACTIVE TOOL CHIP
      ==================================================== */}

      {
        selectedAction !== "message"
        && (

          <div className="tool-chip">


            <span>

              {
                selectedAction === "files"
                  ? "📎 Files"

                  : selectedAction === "library"
                    ? "📚 Library"

                    : selectedAction === "image"
                      ? "🎨 Create image"

                      : selectedAction === "web"
                        ? "🌐 Web search"

                        : "🐙 GitHub"
              }

            </span>


            <button
              type="button"

              title="Remove tool"

              onClick={
                resetTool
              }
            >

              ×

            </button>

          </div>

        )
      }


      {/* ====================================================
          ATTACHED FILES
      ==================================================== */}

      {
        files.length > 0
        && (

          <div className="attached-files">


            {
              files.map(
                (
                  file,
                  index
                ) => (

                  <div

                    className="file-chip"

                    key={
                      `${file.name}-${index}`
                    }

                  >

                    📎 {file.name}

                  </div>

                )
              )
            }


          </div>

        )
      }


      {/* ====================================================
          MAIN COMPOSER
      ==================================================== */}

      <div className="composer">


        {/* ==================================================
            THIS IS THE SAME LEFT-SIDE +
        ================================================== */}

        <button
          type="button"

          className="plus-button"

          title="Add files and more"

          disabled={
            disabled
          }

          aria-label="Add files and more"

          onClick={() =>
            setMenuOpen(
              current =>
                !current
            )
          }
        >

          +

        </button>


        {/* ==================================================
            ASK ME ANYTHING
        ================================================== */}

        <textarea

          value={
            text
          }

          disabled={
            disabled
          }

          placeholder={
            activePlaceholder
          }

          rows={
            1
          }

          onChange={
            event =>
              setText(
                event.target.value
              )
          }

          onKeyDown={
            onKeyDown
          }

        />


        {/* ==================================================
            SEND BUTTON
        ================================================== */}

        <button
          type="button"

          className="send-button"

          title="Send"

          disabled={
            disabled
          }

          aria-label="Send"

          onClick={
            submit
          }
        >

          ➤

        </button>


      </div>


      {/* ====================================================
          HIDDEN FILE INPUT

          Add photos & files click karne par
          THIS PC / Windows picker isi se open hota hai.
      ==================================================== */}

      <input

        ref={
          fileInputRef
        }

        type="file"

        multiple

        hidden

        accept={
          allowedExtensions
            .map(
              extension =>
                `.${extension}`
            )
            .join(",")
        }

        onChange={
          onFileChanged
        }

      />


    </div>
  );
};


export default ChatComposer;
import React from "react";

import {
  createRoot,
  Root
} from "react-dom/client";

import type {
  FrontendRendererArgs,
  FrontendState
} from "@streamlit/component-v2-lib";

import ChatComposer from "./ChatComposer";

import "./style.css";


type SubmissionPayload = {
  action:
    | "message"
    | "files"
    | "library"
    | "image"
    | "web"
    | "github";

  text: string;

  files: Array<{
    name: string;
    type: string;
    size: number;
    data: string;
  }>;
};


type ComposerState =
  FrontendState & {

    submission:
      SubmissionPayload | null;
  };


type ComposerData = {

  placeholder: string;

  disabled: boolean;

  allowedExtensions: string[];
};


let root: Root | null = null;


export default function render(
  args: FrontendRendererArgs<
    ComposerState,
    ComposerData
  >
) {

  const rootElement =
    args.parentElement.querySelector(
      "#chat-composer-root"
    );


  if (!rootElement) {

    console.error(
      "Chat composer root element not found."
    );

    return;
  }


  /*
   * Do not create React root again
   * on every Streamlit rerender.
   */
  if (!root) {

    root = createRoot(
      rootElement
    );
  }


  root.render(

    <React.StrictMode>

      <ChatComposer

        placeholder={
          args.data.placeholder
        }

        disabled={
          args.data.disabled
        }

        allowedExtensions={
          args.data.allowedExtensions
        }

        setTriggerValue={
          args.setTriggerValue
        }

      />

    </React.StrictMode>

  );
}
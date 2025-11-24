import { ProgrammingLanguageOptions } from "@opencanvas/shared/types";
import { ThreadPrimitive, useThreadRuntime, useComposerRuntime } from "@assistant-ui/react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { FC, useMemo, useState } from "react";
import { TighterText } from "../ui/header";
import { FileText, FileUp, Search, AlertCircle } from "lucide-react";
import { Button } from "../ui/button";
import { ContractDropZone } from "./contract-drop-zone";

const CONTRACT_QUESTION_PROMPTS = [
  "What are the termination clauses in this contract?",
  "Explain the liability provisions in this agreement",
  "Identify any non-compete clauses in this document",
  "What are my obligations under this contract?",
  "Summarize the payment terms and conditions",
  "What happens if either party breaches this agreement?",
  "Identify potential legal risks in this contract",
  "Explain the confidentiality provisions in this document",
  "What are the intellectual property rights described here?",
  "What is the governing law for this agreement?",
];

function getRandomPrompts(prompts: string[], count: number = 4): string[] {
  return [...prompts].sort(() => Math.random() - 0.5).slice(0, count);
}

interface QuickStartButtonsProps {
  handleQuickStart: (
    type: "text" | "code",
    language?: ProgrammingLanguageOptions
  ) => void;
  composer: React.ReactNode;
  searchEnabled: boolean;
  handleDocumentUpload: () => void;
}

interface QuickStartPromptsProps {
  searchEnabled: boolean;
  isDocumentUploaded?: boolean;
  uploadedFile?: File | null;
}

const QuickStartPrompts = ({ searchEnabled, isDocumentUploaded, uploadedFile }: QuickStartPromptsProps) => {
  const threadRuntime = useThreadRuntime();

  const handleClick = (text: string) => {
    // Create a message with the example text
    const message: any = {
      role: "user",
      content: [{ type: "text", text }],
    };

    // If a document is uploaded and we have a reference to it, add as attachment
    if (isDocumentUploaded && uploadedFile) {
      message.attachments = [{
        file: uploadedFile,
        name: uploadedFile.name,
        type: uploadedFile.type,
      }];
    }
    
    // Send the message with the attachment if available
    threadRuntime.append(message);
  };

  const selectedPrompts = useMemo(
    () => getRandomPrompts(CONTRACT_QUESTION_PROMPTS),
    [searchEnabled]
  );

  return (
    <div className="flex flex-col w-full gap-2">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 w-full">
        {selectedPrompts.map((prompt, index) => (
          <Button
            key={`quick-start-prompt-${index}`}
            onClick={() => handleClick(prompt)}
            variant="outline"
            className="min-h-[60px] w-full flex items-center justify-center p-6 whitespace-normal text-gray-500 hover:text-gray-700 transition-colors ease-in rounded-2xl"
          >
            <p className="text-center break-words text-sm font-normal">
              {prompt}
            </p>
          </Button>
        ))}
      </div>
    </div>
  );
};

const ContractAnalysisFeatures = () => {
  return (
    <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm hover:shadow transition-all duration-300">
        <div className="flex items-center mb-2 justify-center">
          <div className="bg-gray-100 p-1.5 rounded-full mr-2">
            <FileText className="h-4 w-4 text-gray-600" />
          </div>
          <h3 className="font-medium text-gray-700 text-base text-center">Contract<br />Understanding</h3>
        </div>
        <p className="text-gray-600 text-sm leading-relaxed">PAKTON helps you explore your contracts by identifying obligations, rights, exceptions, and key clauses in an explainable way.</p>
      </div>
      
      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm hover:shadow transition-all duration-300">
        <div className="flex items-center mb-2 justify-center">
          <div className="bg-gray-100 p-1.5 rounded-full mr-2">
            <Search className="h-4 w-4 text-gray-600" />
          </div>
          <h3 className="font-medium text-gray-700 text-base text-center">Question<br />Answering</h3>
        </div>
        <p className="text-gray-600 text-sm leading-relaxed">Αsk questions about your contracts and receive detailed reports grounded in both the document and trusted external legal sources.</p>
      </div>
      
      <div className="bg-white p-5 rounded-lg border border-gray-200 shadow-sm hover:shadow transition-all duration-300">
        <div className="flex items-center mb-2 justify-center">
          <div className="bg-gray-100 p-1.5 rounded-full mr-2">
            <AlertCircle className="h-4 w-4 text-gray-600" />
          </div>
          <h3 className="font-medium text-gray-700 text-base text-center">Explainable<br />Legal Reports</h3>
        </div>
        <p className="text-gray-600 text-sm leading-relaxed">Each answer comes with clear reasoning, cited evidence, and an honest acknowledgment of uncertainty ensuring transparency.</p>
      </div>
    </div>
  );
};

const WhyPakton = () => {
  return (
    <div className="mt-8 bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
      <h3 className="text-xl font-medium text-center text-gray-800 mb-3">But, why PAKTON?</h3>
      <p className="text-gray-700 text-sm leading-relaxed mb-4 text-justify">
        Experimental results show that PAKTON outperforms general-purpose models on contract-related tasks not only in accuracy, but also in explainability, reasoning quality, justification, and the ability to handle ambiguity. 
      </p>
      <div className="flex justify-center gap-3 flex-wrap mb-4">
        <a href="https://pakton.site/evaluation" target="_blank" rel="noopener noreferrer">
          <Button
            variant="outline"
            className="text-gray-700 hover:text-gray-800 transition-colors ease-in rounded-xl flex items-center justify-center gap-2 border-gray-300 hover:border-gray-400 hover:bg-gray-100 px-6 py-2"
          >
            <span>View Evaluation Experiments</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-external-link">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </Button>
        </a>
        <a href="https://github.com/petrosrapto/PAKTON" target="_blank" rel="noopener noreferrer">
          <Button
            variant="outline"
            className="text-gray-700 hover:text-gray-800 transition-colors ease-in rounded-xl flex items-center justify-center gap-2 border-gray-300 hover:border-gray-400 hover:bg-gray-100 px-6 py-2"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            <span>GitHub</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-external-link">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </Button>
        </a>
      </div>
      <p className="text-gray-700 text-sm leading-relaxed mb-4 text-justify">
        PAKTON was published and presented orally at the Main Conference of <strong>Empirical Methods in Natural Language Processing 2025</strong>, demonstrating that it is scientifically validated and peer-reviewed by the research community.
      </p>
      <div className="flex justify-center gap-3 flex-wrap items-center">
        <a href="https://aclanthology.org/2025.emnlp-main.403/" target="_blank" rel="noopener noreferrer">
          <Button
            variant="outline"
            className="text-gray-700 hover:text-gray-800 transition-colors ease-in rounded-xl flex items-center justify-center gap-2 border-gray-300 hover:border-gray-400 hover:bg-gray-100 px-6 py-2"
          >
            <span>View Publication</span>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="feather feather-external-link">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
              <polyline points="15 3 21 3 21 9"></polyline>
              <line x1="10" y1="14" x2="21" y2="3"></line>
            </svg>
          </Button>
        </a>
        <img src="/emnlp_2025_logo_v1.png" alt="EMNLP 2025" className="h-8 opacity-80" />
      </div>
    </div>
  );
};

const QuickStartButtons = (props: QuickStartButtonsProps) => {
  return (
    <div className="flex flex-col gap-6 items-center justify-center w-full">
      <div className="flex flex-col gap-4">
        <p className="text-gray-600 text-sm">Start by uploading a contract document</p>
        <Button
          variant="outline"
          className="text-blue-600 hover:text-blue-700 transition-colors ease-in rounded-2xl flex items-center justify-center gap-2 w-[250px] h-[64px] border-blue-200 hover:border-blue-300 hover:bg-blue-50"
          onClick={props.handleDocumentUpload}
        >
          Upload Contract
          <FileUp className="h-5 w-5" />
        </Button>
      </div>
      <div className="flex flex-col gap-4 mt-2 w-full">
        <p className="text-gray-600 text-sm">Then ask about your contract</p>
        {props.composer}
        <p className="text-gray-600 text-sm mt-2">Or try one of these example questions:</p>
        <QuickStartPrompts searchEnabled={props.searchEnabled} />
      </div>
    </div>
  );
};

interface ThreadWelcomeProps {
  handleQuickStart: (
    type: "text" | "code",
    language?: ProgrammingLanguageOptions
  ) => void;
  composer: React.ReactNode;
  searchEnabled: boolean;
  handleDocumentUpload?: (event: { target: { files: FileList } }) => void;
  isDocumentUploaded?: boolean;
}

export const ThreadWelcome: FC<ThreadWelcomeProps> = (
  props: ThreadWelcomeProps
) => {
  const isDocumentUploaded = props.isDocumentUploaded || false;
  const [uploadedContractFile, setUploadedContractFile] = useState<File | null>(null);
  const composerRuntime = useComposerRuntime();
  
  const handleUpload = (files: FileList, file: File) => {
    // Store the uploaded file for reference
    setUploadedContractFile(file);
    
    // Don't add to composer - we upload directly to Archivist API
    // if (composerRuntime && file) {
    //   composerRuntime.addAttachment(file);
    // }
    
    if (props.handleDocumentUpload) {
      // Create a mock event with the files to pass to the original handler
      const mockEvent = {
        target: {
          files: files
        }
      };
      
      // Call the original handler with our mock event
      props.handleDocumentUpload(mockEvent);
    }
  };
  
  return (
    <ThreadPrimitive.Empty>
      <div className="flex items-center justify-center mt-8 w-full">
        <div className="text-center max-w-3xl w-full">
          {/* Logo and title repositioned to be side by side */}
          <div className="flex items-center justify-center gap-3 mb-2">
            <Avatar className="h-10 w-10 bg-blue-100 ring-2 ring-blue-50">
              {/* <AvatarImage src="/lc_logo.jpg" alt="PAKTON Logo" /> */}
              <AvatarFallback className="text-lg font-bold text-blue-800">📜</AvatarFallback>
            </Avatar>
            <TighterText className="text-2xl font-medium">
              <span style={{ 
                fontFamily: "'Times New Roman', serif", 
                letterSpacing: "0.1em", 
                textTransform: "uppercase",
                fontWeight: "bold",
                textShadow: "1px 1px 1px rgba(0,0,0,0.1)"
              }}>
                PAKTON
              </span>
            </TighterText>
          </div>
          <p className="text-gray-600 mt-2">A Multi-Agent Framework for Question Answering in Long Legal Agreements</p>
          
          <ContractAnalysisFeatures />
          
          <div className="mt-8 w-full">
            {isDocumentUploaded ? (
              // Show chat input and example questions only when document is uploaded
              <div className="flex flex-col gap-4 mt-2 w-full">
                <p className="text-gray-600 text-sm">Ask about your contract</p>
                {props.composer}
                <p className="text-gray-600 text-sm mt-2">Or try one of these example questions:</p>
                <QuickStartPrompts searchEnabled={props.searchEnabled} isDocumentUploaded={isDocumentUploaded} uploadedFile={uploadedContractFile} />
              </div>
            ) : (
              // Show contract upload with drag and drop when no document is uploaded
              <ContractDropZone 
                onUpload={handleUpload}
                isDocumentUploaded={isDocumentUploaded}
              />
            )}
          </div>
          
          {/* Only show WhyPakton when no document is uploaded */}
          {!isDocumentUploaded && <WhyPakton />}
        </div>
      </div>
    </ThreadPrimitive.Empty>
  );
};

"use client";

import { FC, useState, useEffect, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { FileText, Loader2 } from "lucide-react";
import { renderAsync } from "docx-preview";

interface DocumentPreviewDialogProps {
  file: File | null;
  fileName: string;
  children?: React.ReactNode;
}

export const DocumentPreviewDialog: FC<DocumentPreviewDialogProps> = ({
  file,
  fileName,
  children,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const docxContainerRef = useRef<HTMLDivElement>(null);

  const getFileExtension = () => {
    return fileName.split('.').pop()?.toLowerCase() || '';
  };

  useEffect(() => {
    // Cleanup function to revoke object URL when component unmounts or file changes
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [fileUrl]);

  // Effect to handle DOCX rendering when dialog opens
  useEffect(() => {
    let isMounted = true;

    const renderDocx = async () => {
      if (!isOpen || !file) return;

      const extension = getFileExtension();
      const isDocx = extension === 'docx' || file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

      if (!isDocx) {
        // Handle non-DOCX files (PDF, TXT)
        if (!fileUrl) {
            const url = URL.createObjectURL(file);
            setFileUrl(url);
        }
        return;
      }

      // For DOCX
      console.log('Attempting to render DOCX. isOpen:', isOpen, 'Ref:', !!docxContainerRef.current);

      if (!docxContainerRef.current) {
        console.log('Container ref is null, retrying in 100ms...');
        setTimeout(renderDocx, 100);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);
        
        console.log('Starting DOCX rendering...');
        const arrayBuffer = await file.arrayBuffer();
        
        if (!isMounted) return;

        if (!docxContainerRef.current) {
          console.warn('Container ref lost during loading');
          return;
        }

        if (arrayBuffer.byteLength === 0) {
          throw new Error('Document appears to be empty or corrupted');
        }

        // Clear previous content
        docxContainerRef.current.innerHTML = '';

        await renderAsync(arrayBuffer, docxContainerRef.current, undefined, {
          inWrapper: false,
          renderChanges: true,
          renderComments: true,
          experimental: true,
        });
        
        console.log('DOCX rendering completed successfully');
      } catch (error) {
        console.error('Error rendering DOCX:', error);
        if (isMounted) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          setError(`Failed to load document: ${errorMessage}`);
        }
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    if (isOpen) {
      // Small delay to allow DialogContent to mount
      setTimeout(renderDocx, 50);
    } else {
      // Cleanup when closed
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
        setFileUrl(null);
      }
      if (docxContainerRef.current) {
        docxContainerRef.current.innerHTML = '';
      }
      setError(null);
      setIsLoading(false);
    }

    return () => {
      isMounted = false;
    };
  }, [isOpen, file]);

  const handleOpenChange = (open: boolean) => {
    setIsOpen(open);
  };

  const renderPreview = () => {
    const extension = getFileExtension();

    if (error) {
      return (
        <div className="flex items-center justify-center h-[800px] text-red-600">
          <div className="text-center">
            <FileText className="h-16 w-16 mb-4 mx-auto opacity-50" />
            <p className="font-medium">Document Preview Error</p>
            <p className="text-sm mt-2">{error}</p>
          </div>
        </div>
      );
    }

    // For DOCX files - rendered by docx-preview
    if (extension === 'docx' || (file && file.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')) {
      return (
        <div className="relative w-full h-[800px]">
            {isLoading && (
               <div className="absolute inset-0 flex items-center justify-center bg-white z-10">
                  <div className="text-center">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Loading document...</p>
                  </div>
               </div>
            )}
          <style>{`
            .docx-preview ins,
            .docx-preview .ins,
            .docx-preview [data-change="ins"] {
              color: #16a34a !important;
              text-decoration: underline !important;
            }

            .docx-preview del,
            .docx-preview .del,
            .docx-preview [data-change="del"] {
              color: #dc2626 !important;
              text-decoration: line-through !important;
            }

            .docx-preview ins *,
            .docx-preview .ins *,
            .docx-preview [data-change="ins"] * {
              color: inherit !important;
            }
            
            .docx-preview del *,
            .docx-preview .del *,
            .docx-preview [data-change="del"] * {
              color: inherit !important;
            }

            .docx-preview {
              font-family: Calibri, Arial, sans-serif;
              line-height: 1.6;
              color: #000;
              transform: scale(1.2);
              transform-origin: top center;
              margin: 0 auto;
              max-width: 100%;
              padding: 5px;
            }

            .docx-preview-container {
              display: flex;
              justify-content: center;
              align-items: flex-start;
              min-height: 100%;
              padding: 2px;
            }
          `}</style>
          <div className="w-full h-full overflow-auto border rounded bg-white">
            <div className="docx-preview-container overflow-auto" style={{ minHeight: "calc(100% - 0px)" }}>
              <div 
                ref={docxContainerRef}
                className="docx-preview"
              />
            </div>
          </div>
        </div>
      );
    }

    if (isLoading) {
      return (
        <div className="flex items-center justify-center h-[800px]">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
            <p className="text-sm text-gray-600">Loading document...</p>
          </div>
        </div>
      );
    }

    // For PDF files
    if (extension === 'pdf' && fileUrl) {
      return (
        <div className="w-full h-[800px] overflow-auto border rounded bg-white">
          <div className="flex justify-center items-start h-full p-0">
            <iframe
              src={fileUrl}
              className="border-0 rounded shadow-lg"
              style={{ 
                width: '100%', 
                height: '100%', 
                transform: 'scale(1.1)', 
                transformOrigin: 'top center' 
              }}
              title={`Preview of ${fileName}`}
            />
          </div>
        </div>
      );
    }

    // For TXT files - display as text
    if (extension === 'txt' && fileUrl) {
      return (
        <div className="w-full h-[800px] overflow-auto border rounded bg-white">
          <div className="flex justify-center items-start h-full p-0">
            <iframe
              src={fileUrl}
              className="border-0 bg-white rounded shadow-lg"
              style={{ 
                width: '100%', 
                height: '100%', 
                transform: 'scale(1.1)', 
                transformOrigin: 'top center',
                fontSize: '16px'
              }}
              title={`Preview of ${fileName}`}
            />
          </div>
        </div>
      );
    }

    // Fallback for unsupported types
    return (
      <div className="flex flex-col items-center justify-center h-[800px] text-gray-500">
        <FileText className="h-16 w-16 mb-4" />
        <p>Preview not available for this file type</p>
        <p className="text-sm mt-2">{fileName}</p>
      </div>
    );
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogTrigger asChild>
        {children || (
          <button className="flex items-center gap-2 bg-blue-50 text-blue-700 px-3 py-1.5 rounded-full text-sm border border-blue-200 hover:bg-blue-100 transition-colors cursor-pointer">
            <FileText className="h-4 w-4" />
            <span className="font-medium">{fileName}</span>
          </button>
        )}
      </DialogTrigger>
      <DialogContent className="max-w-7xl w-[95vw] max-h-[95vh] p-0" aria-describedby="document-preview-description">
        <DialogHeader className="p-2 pb-0">
          <DialogTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            {fileName}
          </DialogTitle>
          <div id="document-preview-description" className="sr-only">
            Preview of {fileName}
          </div>
        </DialogHeader>
        <div className="px-2 pb-2">
          {renderPreview()}
        </div>
      </DialogContent>
    </Dialog>
  );
};

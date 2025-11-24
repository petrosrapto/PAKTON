"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';

interface DocumentContextType {
  uploadedFileName: string | null;
  setUploadedFileName: (fileName: string | null) => void;
  uploadedFile: File | null;
  setUploadedFile: (file: File | null) => void;
  isDocumentUploaded: boolean;
  setIsDocumentUploaded: (uploaded: boolean) => void;
}

const DocumentContext = createContext<DocumentContextType | undefined>(undefined);

export function DocumentProvider({ children }: { children: ReactNode }) {
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isDocumentUploaded, setIsDocumentUploaded] = useState(false);

  return (
    <DocumentContext.Provider 
      value={{ 
        uploadedFileName, 
        setUploadedFileName,
        uploadedFile,
        setUploadedFile,
        isDocumentUploaded,
        setIsDocumentUploaded
      }}
    >
      {children}
    </DocumentContext.Provider>
  );
}

export function useDocumentContext() {
  const context = useContext(DocumentContext);
  if (context === undefined) {
    throw new Error('useDocumentContext must be used within a DocumentProvider');
  }
  return context;
}
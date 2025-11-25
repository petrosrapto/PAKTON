import {
  CustomQuickAction,
  Reflections,
  ContextDocument,
} from "@opencanvas/shared/types";
import { useState } from "react";
import { useToast } from "./use-toast";

export function useStore() {
  const { toast } = useToast();
  const [isLoadingReflections, setIsLoadingReflections] = useState(false);
  const [isLoadingQuickActions, setIsLoadingQuickActions] = useState(false);
  const [reflections, setReflections] = useState<
    Reflections & { assistantId: string; updatedAt: Date }
  >();

  const getReflections = async (assistantId: string): Promise<void> => {
    // Stubbed: LangGraph store removed
    setIsLoadingReflections(false);
    setReflections(undefined);
  };

  const deleteReflections = async (assistantId: string): Promise<boolean> => {
    // Stubbed: LangGraph store removed
    setReflections(undefined);
    return true;
  };

  const getCustomQuickActions = async (
    userId: string
  ): Promise<CustomQuickAction[] | undefined> => {
    // Stubbed: LangGraph store removed
    setIsLoadingQuickActions(false);
    return undefined;
  };

  const deleteCustomQuickAction = async (
    id: string,
    rest: CustomQuickAction[],
    userId: string
  ): Promise<boolean> => {
    // Stubbed: LangGraph store removed
    return true;
  };

  const createCustomQuickAction = async (
    newAction: CustomQuickAction,
    rest: CustomQuickAction[],
    userId: string
  ): Promise<boolean> => {
    // Stubbed: LangGraph store removed
    return true;
  };

  const editCustomQuickAction = async (
    editedAction: CustomQuickAction,
    rest: CustomQuickAction[],
    userId: string
  ): Promise<boolean> => {
    // Stubbed: LangGraph store removed
    return true;
  };

  const putContextDocuments = async ({
    assistantId,
    documents,
  }: {
    assistantId: string;
    documents: ContextDocument[];
  }): Promise<void> => {
    // Stubbed: LangGraph store removed
  };

  const getContextDocuments = async (
    assistantId: string
  ): Promise<ContextDocument[] | undefined> => {
    // Stubbed: LangGraph store removed
    return undefined;
  };

  return {
    isLoadingReflections,
    reflections,
    isLoadingQuickActions,
    deleteReflections,
    getReflections,
    deleteCustomQuickAction,
    getCustomQuickActions,
    editCustomQuickAction,
    createCustomQuickAction,
    putContextDocuments,
    getContextDocuments,
  };
}

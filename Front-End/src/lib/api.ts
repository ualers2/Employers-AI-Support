// src/lib/api.ts

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

// New interfaces for ConfigPanel
export interface BotConfig {
    telegramBotToken: string; // Renamed from botToken
    telegramChannelId: string; // Renamed from channelId
    discordBotToken?: string; // New: Optional for Discord
    discordChannelId?: string; // New: Optional for Discord
    // Novos campos para WhatsApp
    waServerUrl: string;
    waInstanceId: string;
    waApiKey: string;
    waSupportGroupJid: string;
}
export interface ModerationConfig {
    autoModeration: boolean;
    aiModeration: boolean;
    aiModerationModel: string; // e.g., 'ominilatest', 'gpt-4', 'claude-3'
    deleteSpam: boolean;
    banThreshold: number;
}

export interface AlfredConfig {
    alfredName: string;
    alfredModel: string; // e.g., 'gpt-4.1-nano', 'gpt-4.1', 'gpt-4o'
    alfredInstructions: string;
    toolsEnabled: boolean;
}

export interface FullBotConfiguration {
    botConfig: BotConfig;
    moderationConfig: ModerationConfig;
    alfredConfig: AlfredConfig;
}

interface RealtimeMetrics {
    messagesPerHour: number;
    onlineUsers: number;
    averageResponseTime: number;
}

export interface Activity {
    id: string;
    timestamp: string;
    type: "message" | "ban" | "unban" | "file" | "response" | "error" | "info";
    user: string;
    action: string;
    details: string;
    status: "success" | "warning" | "info" | "error";
}

interface ActivityLogResponse {
    total: number;
    activities: Activity[];
}
// --- New/Updated Interface for Recent Messages ---
export interface RecentMessage {
    id: string; // Unique identifier for the message/interaction
    user: string; // Display name of the user
    userId: string; // User's ID or handle (e.g., @username)
    message: string; // The content of the message
    timestamp: string; // Timestamp of the message (ISO string or similar)
    status: "responded" | "pending" | "resolved"; // Status of the interaction
}

// --- Alfred File Management Interface and API Functions ---
// Updated AlfredFile interface to match backend response keys more closely
export interface AlfredFile {
    id: string; // This will be the unique_filename from backend
    name: string; // This will be the originalFileName from backend
    type: string; // e.g., "document", "image", etc. (inferred or based on file extension)
    size: string; // e.g., "15.2 KB"
    lastModified: string; // ISO string
    url?: string; // Optional: Backend provides a download URL
    content?: string; // Optional: Only present when viewing/editing
    isEditing?: boolean; // Frontend specific state
}

// --- New API Function for Recent Messages ---
export const fetchRecentMessages = async (): Promise<RecentMessage[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/messages/recent`); // New endpoint
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: RecentMessage[] = await response.json();
        return data;
    } catch (error) {
        console.error("Error fetching recent messages:", error);
        throw error;
    }
};
export const uploadAlfredFile = async (file: File, caption: string = '', channelId: string = ''): Promise<{ message: string; fileId: string; fileName: string; size: string; lastModified: string }> => {
    try {
        const formData = new FormData();
        formData.append('file', file);
        if (caption) formData.append('caption', caption);
        if (channelId) formData.append('channelId', channelId);

        const response = await fetch(`${API_BASE_URL}/alfred-files/upload`, { // Updated endpoint
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error("Error uploading Alfred file:", error);
        throw error;
    }
};

export const fetchAlfredFiles = async (): Promise<AlfredFile[]> => {
    try {
        const response = await fetch(`${API_BASE_URL}/alfred-files`); // Updated endpoint
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: AlfredFile[] = await response.json(); // Backend now returns a list directly
        return data; // Data should already match AlfredFile structure
    } catch (error) {
        console.error("Error fetching Alfred files:", error);
        throw error;
    }
};

export const fetchAlfredFileContent = async (fileId: string): Promise<{ id: string; name: string; content: string; lastModified: string }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/alfred-files/${fileId}/content`); // Updated endpoint
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json(); // Backend returns JSON with content and metadata
    } catch (error) {
        console.error(`Error fetching content for file ID ${fileId}:`, error);
        throw error;
    }
};

export const updateAlfredFileContent = async (fileId: string, content: string): Promise<{ message: string; fileId: string; lastModified: string }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/alfred-files/${fileId}/content`, { // Updated endpoint
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error updating content for file ID ${fileId}:`, error);
        throw error;
    }
};

export const deleteAlfredFile = async (fileId: string): Promise<{ message: string }> => {
    try {
        const response = await fetch(`${API_BASE_URL}/alfred-files/${fileId}`, { // Updated endpoint
            method: 'DELETE',
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error deleting file with ID ${fileId}:`, error);
        throw error;
    }
};


export const fetchBotConfiguration = async (): Promise<FullBotConfiguration> => {
    const response = await fetch(`${API_BASE_URL}/config`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    // Map backend flat response to new front-end shape
    const telegramBotToken = data.botConfig?.botToken ?? data.botToken ?? '';
    const telegramChannelId = data.botConfig?.channelId ?? data.channelId ?? '';
    const discordBotToken = data.botConfig?.discordBotToken ?? data.discordBotToken ?? '';
    const discordChannelId = data.botConfig?.discordChannelId ?? data.discordChannelId ?? '';
    const autoModeration = data.moderationConfig?.autoModeration ?? data.autoModeration ?? false;
    const aiModeration = data.moderationConfig?.aiModeration ?? data.aiModeration ?? false;
    const aiModerationModel = data.moderationConfig?.aiModerationModel ?? data.aiModerationModel ?? 'ominilatest';
    const deleteSpam = data.moderationConfig?.deleteSpam ?? data.deleteSpam ?? false;
    const banThreshold = data.moderationConfig?.banThreshold ?? data.banThreshold ?? 3;
    const alfredName = data.alfredConfig?.alfredName ?? data.alfredName ?? 'Alfred';
    const alfredModel = data.alfredConfig?.alfredModel ?? data.alfredModel ?? 'gpt-4.1-nano';
    const alfredInstructions = data.alfredConfig?.alfredInstructions ?? data.alfredInstructions ?? '';
    const toolsEnabled = data.alfredConfig?.toolsEnabled ?? data.toolsEnabled ?? false;
    const waServerUrl       = data.botConfig?.waServerUrl       ?? data.waServerUrl       ?? '';
    const waInstanceId      = data.botConfig?.waInstanceId      ?? data.waInstanceId      ?? '';
    const waApiKey          = data.botConfig?.waApiKey          ?? data.waApiKey          ?? '';
    const waSupportGroupJid = data.botConfig?.waSupportGroupJid ?? data.waSupportGroupJid ?? '';

    return {
        botConfig: { telegramBotToken, telegramChannelId, 
            discordBotToken, discordChannelId,
            waServerUrl, waInstanceId, waApiKey, waSupportGroupJid
        },
        moderationConfig: { autoModeration, aiModeration, aiModerationModel, deleteSpam, banThreshold },
        alfredConfig: { alfredName, alfredModel, alfredInstructions, toolsEnabled }
    };
};

export const updateBotConfiguration = async (config: FullBotConfiguration): Promise<FullBotConfiguration> => {
    // Flatten into backend expected keys
    const payload: any = {
        botToken: config.botConfig.telegramBotToken,
        channelId: config.botConfig.telegramChannelId,
        waServerUrl:       config.botConfig.waServerUrl,      
        waInstanceId:      config.botConfig.waInstanceId,
        waApiKey:          config.botConfig.waApiKey,
        waSupportGroupJid: config.botConfig.waSupportGroupJid,
        autoModeration: config.moderationConfig.autoModeration,
        aiModeration: config.moderationConfig.aiModeration,
        aiModerationModel: config.moderationConfig.aiModerationModel,
        deleteSpam: config.moderationConfig.deleteSpam,
        banThreshold: config.moderationConfig.banThreshold,
        alfredName: config.alfredConfig.alfredName,
        alfredModel: config.alfredConfig.alfredModel,
        alfredInstructions: config.alfredConfig.alfredInstructions,
        toolsEnabled: config.alfredConfig.toolsEnabled,
    };
    // Include Discord keys if provided
    if (config.botConfig.discordBotToken) payload.discordBotToken = config.botConfig.discordBotToken;
    if (config.botConfig.discordChannelId) payload.discordChannelId = config.botConfig.discordChannelId;



    const response = await fetch(`${API_BASE_URL}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    // Refetch to sync
    return await fetchBotConfiguration();
};


export const fetchRealtimeMetrics = async (): Promise<RealtimeMetrics> => {
    const response = await fetch(`${API_BASE_URL}/metrics/realtime`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
};

export const fetchActivityLog = async (
    limit: number = 10,
    offset: number = 0,
    filters?: { type?: string; status?: string; startDate?: string; endDate?: string; searchTerm?: string; }
): Promise<ActivityLogResponse> => {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    if (filters) {
        for (const key in filters) {
            const value = filters[key as keyof typeof filters];
            if (value) params.append(key, value);
        }
    }
    const response = await fetch(`${API_BASE_URL}/activities?${params.toString()}`);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
};

export const clearActivityLog = async (beforeDate?: string, status?: string): Promise<{ message: string; deletedCount: number }> => {
    const params = new URLSearchParams();
    if (beforeDate) params.append('beforeDate', beforeDate);
    if (status) params.append('status', status);
    const response = await fetch(`${API_BASE_URL}/activities?${params.toString()}`, { method: 'DELETE' });
    if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    return await response.json();
};

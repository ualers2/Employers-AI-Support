import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { useToast } from "@/hooks/use-toast";
import { Upload, FileText, Download, Trash2, Eye, Edit, Save, Loader2, X } from "lucide-react"; // Added X for close button

import {
    uploadAlfredFile,
    fetchAlfredFiles,
    fetchAlfredFileContent,
    updateAlfredFileContent,
    deleteAlfredFile,
    AlfredFile // Import the updated interface
} from '@/lib/api';

const FileManager = () => {
    const [caption, setCaption] = useState('');
    const [channelId, setChannelId] = useState('');
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { toast } = useToast();

    const [alfredFiles, setAlfredFiles] = useState<AlfredFile[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [viewingFile, setViewingFile] = useState<AlfredFile | null>(null); // State for viewing content
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';

    // Function to fetch files
    const loadAlfredFiles = async () => {
        setLoading(true);
        setError(null);
        try {
            const files = await fetchAlfredFiles();
            setAlfredFiles(files.map(file => ({ ...file, isEditing: false }))); // Add isEditing state
        } catch (err: any) {
            setError(err.message || "Failed to fetch files.");
            toast({
                title: "Erro ao carregar arquivos",
                description: err.message || "Não foi possível carregar a lista de arquivos do Alfred.",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    // Load files on component mount
    useEffect(() => {
        loadAlfredFiles();
    }, []);

    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setLoading(true);
        setError(null);
        try {
            const response = await uploadAlfredFile(file, caption, channelId);

            // Create a new AlfredFile object from the backend response
            const newFile: AlfredFile = {
                id: response.fileId,
                name: response.fileName,
                type: response.fileName.split('.').pop() || 'document', // Infer type from extension
                size: response.size,
                lastModified: response.lastModified,
                url: `${API_BASE_URL}/alfred-files/${response.fileId}/download`, // Construct download URL
                isEditing: false
            };

            setAlfredFiles(prevFiles => [newFile, ...prevFiles]); // Add new file to the list
            toast({
                title: "Arquivo do Alfred carregado!",
                description: `${newFile.name} foi carregado com sucesso.`,
            });
            setCaption('');
            setChannelId('');
        } catch (err: any) {
            setError(err.message || "Failed to upload file.");
            toast({
                title: "Erro ao carregar arquivo",
                description: err.message || "Não foi possível carregar o arquivo para o Alfred.",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = ''; // Clear the input
            }
        }
    };

    const handleEditFile = async (fileId: string) => {
        setLoading(true);
        setError(null);
        try {
            const { content, lastModified } = await fetchAlfredFileContent(fileId);
            setAlfredFiles(files =>
                files.map(file =>
                    file.id === fileId ? { ...file, isEditing: true, content: content, lastModified: lastModified } : file
                )
            );
        } catch (err: any) {
            setError(err.message || "Failed to fetch file content.");
            toast({
                title: "Erro ao editar arquivo",
                description: err.message || `Não foi possível carregar o conteúdo do arquivo.`,
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    const handleSaveFile = async (fileId: string, content: string) => {
        setLoading(true);
        setError(null);
        try {
            const { lastModified } = await updateAlfredFileContent(fileId, content);
            setAlfredFiles(files =>
                files.map(file =>
                    file.id === fileId ? { ...file, isEditing: false, content: content, lastModified: lastModified } : file
                )
            );
            toast({
                title: "Arquivo salvo!",
                description: "As alterações foram salvas no agente Alfred.",
            });
        } catch (err: any) {
            setError(err.message || "Failed to save file.");
            toast({
                title: "Erro ao salvar arquivo",
                description: err.message || "Não foi possível salvar as alterações.",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    const handleViewFile = async (fileId: string) => {
        setLoading(true);
        setError(null);
        try {
            const { content, name, lastModified } = await fetchAlfredFileContent(fileId);
            setViewingFile({
                id: fileId,
                name: name,
                type: name.split('.').pop() || 'document', // Infer type
                size: '', // Size is not available directly from this endpoint
                lastModified: lastModified,
                content: content
            });
        } catch (err: any) {
            setError(err.message || "Failed to fetch file content.");
            toast({
                title: "Erro ao visualizar arquivo",
                description: err.message || "Não foi possível carregar o conteúdo do arquivo.",
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    const handleDownloadFile = (fileId: string) => {
        // Construct the download URL based on the new endpoint structure
        window.open(`${API_BASE_URL}/alfred-files/${fileId}/download`, '_blank');
        toast({
            title: "Download iniciado!",
            description: "O download do arquivo foi iniciado.",
        });
    };

    const handleDeleteFile = async (fileId: string, fileName: string) => {
        if (!window.confirm(`Tem certeza que deseja deletar o arquivo "${fileName}"?`)) {
            return;
        }
        setLoading(true);
        setError(null);
        try {
            await deleteAlfredFile(fileId);
            setAlfredFiles(prevFiles => prevFiles.filter(file => file.id !== fileId));
            toast({
                title: "Arquivo deletado!",
                description: `${fileName} foi removido com sucesso.`,
            });
            // If the deleted file was being viewed, close the viewer
            if (viewingFile && viewingFile.id === fileId) {
                setViewingFile(null);
            }
        } catch (err: any) {
            setError(err.message || "Failed to delete file.");
            toast({
                title: "Erro ao deletar arquivo",
                description: err.message || `Não foi possível deletar o arquivo ${fileName}.`,
                variant: "destructive"
            });
        } finally {
            setLoading(false);
        }
    };

    const handleContentChange = (fileId: string, newContent: string) => {
        setAlfredFiles(files =>
            files.map(file =>
                file.id === fileId ? { ...file, content: newContent } : file
            )
        );
    };

    const getFileIcon = (type: string) => {
        // You can enhance this with more specific icons based on file extensions
        switch (type) {
            case 'pdf':
                return <FileText className="w-4 h-4 text-red-500" />;
            case 'docx':
                return <FileText className="w-4 h-4 text-blue-500" />;
            case 'csv':
                return <FileText className="w-4 h-4 text-green-500" />;
            case 'json':
                return <FileText className="w-4 h-4 text-yellow-500" />;
            default:
                return <FileText className="w-4 h-4" />;
        }
    };

    const getFileTypeBadge = (type: string) => {
        return <Badge variant="secondary">Alfred</Badge>;
    };

    return (
        <div className="space-y-6">
            {/* Upload Section */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Upload className="w-5 h-5" />
                        Mantenha os Arquivos do Alfred Atualizados
                    </CardTitle>
                    <CardDescription>
                        Carregue novos arquivos para a base de conhecimento do agente Alfred
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">

                    <div className="flex gap-2">
                        <Button onClick={() => fileInputRef.current?.click()} className="flex-1" disabled={loading}>
                            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="w-4 h-4 mr-2" />}
                            Carregar Arquivo do Alfred
                        </Button>
                        <input
                            ref={fileInputRef}
                            type="file"
                            onChange={handleFileUpload}
                            className="hidden"
                            accept=".md,.txt,.pdf,.docx,.csv,.json" // Updated allowed types
                        />
                    </div>
                    {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
                </CardContent>
            </Card>

            {/* Alfred Files Library */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <FileText className="w-5 h-5" />
                        Base de Conhecimento do Alfred
                    </CardTitle>
                    <CardDescription>
                        Arquivos que alimentam a inteligência do agente Alfred
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    {loading && alfredFiles.length === 0 ? (
                        <div className="flex items-center justify-center h-24">
                            <Loader2 className="mr-2 h-6 w-6 animate-spin" /> Carregando arquivos...
                        </div>
                    ) : error && alfredFiles.length === 0 ? (
                        <div className="text-red-500 text-center py-4">{error}</div>
                    ) : alfredFiles.length === 0 ? (
                        <p className="text-center text-muted-foreground py-4">Nenhum arquivo encontrado para Alfred. Comece carregando um!</p>
                    ) : (
                        <div className="space-y-4">
                            {alfredFiles.map((file, index) => (
                                <div key={file.id}>
                                    <div className="flex items-start justify-between space-x-4">
                                        <div className="flex items-center gap-3 flex-1">
                                            {getFileIcon(file.type)}
                                            <div className="flex-1 space-y-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="font-medium">{file.name}</span>
                                                    {getFileTypeBadge(file.type)}
                                                </div>
                                                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                                    <span>{file.size}</span>
                                                    <span>Modificado: {new Date(file.lastModified).toLocaleString()}</span>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex flex-wrap gap-2 justify-end">
                                            {file.isEditing ? (
                                                <Button variant="default" size="sm" onClick={() => handleSaveFile(file.id, file.content || '')} disabled={loading}>
                                                    <Save className="w-4 h-4 mr-1" />
                                                    Salvar
                                                </Button>
                                            ) : (
                                                <>
                                                    <Button variant="outline" size="sm" onClick={() => handleViewFile(file.id)} disabled={loading}>
                                                        <Eye className="w-4 h-4 mr-1" />
                                                        Visualizar
                                                    </Button>
                                                    <Button variant="outline" size="sm" onClick={() => handleEditFile(file.id)} disabled={loading}>
                                                        <Edit className="w-4 h-4 mr-1" />
                                                        Editar
                                                    </Button>
                                                </>
                                            )}
                                            <Button variant="outline" size="sm" onClick={() => handleDownloadFile(file.id)} disabled={loading}>
                                                <Download className="w-4 h-4 mr-1" />
                                                Baixar
                                            </Button>
                                            <Button variant="destructive" size="sm" onClick={() => handleDeleteFile(file.id, file.name)} disabled={loading}>
                                                <Trash2 className="w-4 h-4 mr-1" />
                                                Deletar
                                            </Button>
                                        </div>
                                    </div>
                                    {file.isEditing && (
                                        <div className="mt-4">
                                            <Textarea
                                                value={file.content || ''}
                                                onChange={(e) => handleContentChange(file.id, e.target.value)}
                                                rows={10}
                                                className="font-mono text-sm"
                                            />
                                        </div>
                                    )}
                                    {index < alfredFiles.length - 1 && <Separator className="mt-4" />}
                                </div>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* File Viewer Modal */}
            {viewingFile && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                        <CardHeader className="flex flex-row items-center justify-between">
                            <CardTitle className="text-lg">{viewingFile.name}</CardTitle>
                            <Button variant="ghost" size="sm" onClick={() => setViewingFile(null)}>
                                <X className="h-5 w-5" />
                            </Button>
                        </CardHeader>
                        <CardContent>
                            <pre className="whitespace-pre-wrap font-mono text-sm bg-gray-50 p-4 rounded-md">
                                {viewingFile.content || 'Nenhum conteúdo para visualizar.'}
                            </pre>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
};

export default FileManager;
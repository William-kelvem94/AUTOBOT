"""
AUTOBOT React Frontend - Interface Principal
============================================

Interface web moderna e responsiva para o sistema AUTOBOT.
Integração completa com o backend Flask e sistema de IA local.

Componentes principais:
- Dashboard de monitoramento
- Gerenciamento de automações
- Interface de chat com IA
- Configurações de integrações
- Visualização de métricas e logs
"""

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useNavigate,
  useLocation
} from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
  Grid,
  Paper,
  Card,
  CardContent,
  CardActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Alert,
  IconButton,
  Menu,
  MenuItem,
  Switch,
  FormControlLabel,
  Chip,
  LinearProgress,
  CircularProgress,
  Tabs,
  Tab,
  Box,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Tooltip,
  Badge,
  Avatar,
  FormControl,
  InputLabel,
  Select,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Menu as MenuIcon,
  Notifications as NotificationsIcon,
  AccountCircle as AccountIcon,
  ExitToApp as LogoutIcon,
  Chat as ChatIcon,
  Analytics as AnalyticsIcon,
  Integration as IntegrationIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  CloudDone as CloudIcon,
  Error as ErrorIcon,
  CheckCircle as SuccessIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon
} from '@mui/icons-material';
import {
  createTheme,
  ThemeProvider,
  styled
} from '@mui/material/styles';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { format, subDays, subHours } from 'date-fns';
import { ptBR } from 'date-fns/locale';

// Configuração do tema Material-UI
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
      dark: '#115293',
      light: '#42a5f5'
    },
    secondary: {
      main: '#dc004e',
      dark: '#9a0036',
      light: '#e33371'
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff'
    },
    success: {
      main: '#2e7d32'
    },
    warning: {
      main: '#ed6c02'
    },
    error: {
      main: '#d32f2f'
    }
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h4: {
      fontWeight: 600
    },
    h5: {
      fontWeight: 500
    },
    h6: {
      fontWeight: 500
    }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 8
        }
      }
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 12
        }
      }
    }
  }
});

// Configuração do Axios
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Interceptor para adicionar token de autenticação
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Context para autenticação
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('authToken');
    const userData = localStorage.getItem('userData');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const login = async (username, password) => {
    try {
      const response = await api.post('/api/auth/login', { username, password });
      const { token, user: userData } = response.data;
      
      localStorage.setItem('authToken', token);
      localStorage.setItem('userData', JSON.stringify(userData));
      setUser(userData);
      
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Erro ao fazer login' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    setUser(null);
  };

  const register = async (username, email, password) => {
    try {
      await api.post('/api/auth/register', { username, email, password });
      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error.response?.data?.error || 'Erro ao registrar' 
      };
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de AuthProvider');
  }
  return context;
};

// Componente de Login
const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      if (isRegister) {
        const result = await register(username, email, password);
        if (result.success) {
          setSuccess('Usuário registrado com sucesso! Faça login.');
          setIsRegister(false);
        } else {
          setError(result.error);
        }
      } else {
        const result = await login(username, password);
        if (!result.success) {
          setError(result.error);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={6} sx={{ p: 4, borderRadius: 3 }}>
        <Box textAlign="center" mb={3}>
          <Typography variant="h4" component="h1" gutterBottom color="primary">
            🤖 AUTOBOT
          </Typography>
          <Typography variant="h6" color="textSecondary">
            Sistema Completo de IA Local Corporativa
          </Typography>
        </Box>

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Usuário"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
            required
            variant="outlined"
          />
          
          {isRegister && (
            <TextField
              fullWidth
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              margin="normal"
              required
              variant="outlined"
            />
          )}
          
          <TextField
            fullWidth
            label="Senha"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
            variant="outlined"
          />

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mt: 2 }}>
              {success}
            </Alert>
          )}

          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={loading}
            sx={{ mt: 3, mb: 2, py: 1.5 }}
          >
            {loading ? (
              <CircularProgress size={24} />
            ) : (
              isRegister ? 'Registrar' : 'Entrar'
            )}
          </Button>

          <Button
            fullWidth
            variant="text"
            onClick={() => setIsRegister(!isRegister)}
            disabled={loading}
          >
            {isRegister ? 'Já tem conta? Faça login' : 'Não tem conta? Registre-se'}
          </Button>
        </form>
      </Paper>
    </Container>
  );
};

// Componente de Dashboard Principal
const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('24h');

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      const [statsResponse, metricsResponse] = await Promise.all([
        api.get('/api/dashboard/stats'),
        api.get(`/api/metrics/system?period=${period}`)
      ]);
      
      setStats(statsResponse.data);
      setMetrics(metricsResponse.data);
    } catch (error) {
      console.error('Erro ao carregar dashboard:', error);
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 30000); // Atualiza a cada 30s
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  if (loading && !stats) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress size={60} />
      </Box>
    );
  }

  const getStatusColor = (value, threshold = 80) => {
    if (value > threshold) return 'error';
    if (value > threshold * 0.7) return 'warning';
    return 'success';
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Período</InputLabel>
          <Select
            value={period}
            label="Período"
            onChange={(e) => setPeriod(e.target.value)}
          >
            <MenuItem value="1h">1 Hora</MenuItem>
            <MenuItem value="24h">24 Horas</MenuItem>
            <MenuItem value="7d">7 Dias</MenuItem>
            <MenuItem value="30d">30 Dias</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {/* Cards de Estatísticas */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Automações Total
                  </Typography>
                  <Typography variant="h4">
                    {stats?.automations?.total || 0}
                  </Typography>
                </Box>
                <PlayIcon color="primary" sx={{ fontSize: 48 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Taxa de Sucesso
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {stats?.automations?.success_rate?.toFixed(1) || 0}%
                  </Typography>
                </Box>
                <SuccessIcon color="success" sx={{ fontSize: 48 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Usuários Ativos
                  </Typography>
                  <Typography variant="h4">
                    {stats?.users?.active || 0}
                  </Typography>
                </Box>
                <AccountIcon color="secondary" sx={{ fontSize: 48 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Últimas 24h
                  </Typography>
                  <Typography variant="h4">
                    {stats?.automations?.last_24h || 0}
                  </Typography>
                </Box>
                <SpeedIcon color="info" sx={{ fontSize: 48 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Métricas do Sistema */}
      <Grid container spacing={3} mb={4}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                CPU Usage
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Box flex={1}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics?.metrics?.cpu_usage?.average || 0}
                    color={getStatusColor(metrics?.metrics?.cpu_usage?.average || 0)}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
                <Typography variant="body2">
                  {metrics?.metrics?.cpu_usage?.average?.toFixed(1) || 0}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Memory Usage
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Box flex={1}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics?.metrics?.memory_usage?.average || 0}
                    color={getStatusColor(metrics?.metrics?.memory_usage?.average || 0)}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
                <Typography variant="body2">
                  {metrics?.metrics?.memory_usage?.average?.toFixed(1) || 0}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Disk Usage
              </Typography>
              <Box display="flex" alignItems="center" gap={2}>
                <Box flex={1}>
                  <LinearProgress
                    variant="determinate"
                    value={metrics?.metrics?.disk_usage?.average || 0}
                    color={getStatusColor(metrics?.metrics?.disk_usage?.average || 0)}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
                <Typography variant="body2">
                  {metrics?.metrics?.disk_usage?.average?.toFixed(1) || 0}%
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Integrações Mais Usadas */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Integrações Mais Usadas
              </Typography>
              {stats?.top_integrations?.length > 0 ? (
                <List>
                  {stats.top_integrations.map((integration, index) => (
                    <ListItem key={integration.name} sx={{ px: 0 }}>
                      <ListItemText
                        primary={integration.name.toUpperCase()}
                        secondary={`${integration.count} execuções`}
                      />
                      <Chip 
                        label={`#${index + 1}`} 
                        size="small" 
                        color="primary" 
                        variant="outlined"
                      />
                    </ListItem>
                  ))}
                </List>
              ) : (
                <Typography color="textSecondary">
                  Nenhuma integração executada recentemente
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status do Sistema
              </Typography>
              <List>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <CloudIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="API Backend"
                    secondary="Operacional"
                  />
                  <Chip label="Online" color="success" size="small" />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <StorageIcon color="success" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Banco de Dados"
                    secondary="Conectado"
                  />
                  <Chip label="OK" color="success" size="small" />
                </ListItem>
                <ListItem sx={{ px: 0 }}>
                  <ListItemIcon>
                    <MemoryIcon color="warning" />
                  </ListItemIcon>
                  <ListItemText
                    primary="Sistema de IA"
                    secondary="Iniciando..."
                  />
                  <Chip label="Carregando" color="warning" size="small" />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

// Componente de Automações
const Automations = () => {
  const [integrations, setIntegrations] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedIntegration, setSelectedIntegration] = useState('');
  const [selectedAction, setSelectedAction] = useState('');
  const [parameters, setParameters] = useState('{}');
  const [loading, setLoading] = useState(false);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Ações disponíveis por integração
  const availableActions = {
    bitrix24: ['create_lead', 'get_deals', 'update_contact'],
    ixcsoft: ['get_clients', 'create_ticket', 'get_invoices'],
    locaweb: ['get_domains', 'check_hosting'],
    fluctus: ['get_analysis', 'create_report'],
    newave: ['get_energy_data', 'generate_forecast'],
    uzera: ['sync_products', 'update_inventory'],
    playhub: ['get_analytics', 'update_games']
  };

  useEffect(() => {
    fetchIntegrations();
    fetchLogs();
  }, [page, rowsPerPage]);

  const fetchIntegrations = async () => {
    try {
      const response = await api.get('/api/integrations');
      setIntegrations(response.data.integrations);
    } catch (error) {
      console.error('Erro ao carregar integrações:', error);
    }
  };

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const response = await api.get(`/api/automations/logs?page=${page + 1}&per_page=${rowsPerPage}`);
      setLogs(response.data.logs);
    } catch (error) {
      console.error('Erro ao carregar logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const executeAutomation = async () => {
    if (!selectedIntegration || !selectedAction) {
      setSnackbar({
        open: true,
        message: 'Selecione uma integração e ação',
        severity: 'warning'
      });
      return;
    }

    try {
      setExecuteLoading(true);
      const parsedParameters = JSON.parse(parameters);
      
      const response = await api.post('/api/automations/execute', {
        integration: selectedIntegration,
        action: selectedAction,
        parameters: parsedParameters
      });

      if (response.data.status === 'success') {
        setSnackbar({
          open: true,
          message: 'Automação executada com sucesso!',
          severity: 'success'
        });
        fetchLogs(); // Recarrega os logs
      } else {
        setSnackbar({
          open: true,
          message: response.data.message || 'Erro na automação',
          severity: 'error'
        });
      }
    } catch (error) {
      console.error('Erro ao executar automação:', error);
      setSnackbar({
        open: true,
        message: 'Erro ao executar automação',
        severity: 'error'
      });
    } finally {
      setExecuteLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <SuccessIcon color="success" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <WarningIcon color="warning" />;
    }
  };

  const getStatusChip = (status) => {
    const colors = {
      success: 'success',
      error: 'error',
      warning: 'warning'
    };
    
    return (
      <Chip 
        label={status} 
        color={colors[status] || 'default'} 
        size="small"
        variant="outlined"
      />
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Automações
      </Typography>

      {/* Formulário de Execução */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Executar Automação
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Integração</InputLabel>
                <Select
                  value={selectedIntegration}
                  label="Integração"
                  onChange={(e) => {
                    setSelectedIntegration(e.target.value);
                    setSelectedAction(''); // Reset action when integration changes
                  }}
                >
                  {integrations.filter(i => i.enabled).map((integration) => (
                    <MenuItem key={integration.name} value={integration.name}>
                      {integration.name.toUpperCase()}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={4}>
              <FormControl fullWidth disabled={!selectedIntegration}>
                <InputLabel>Ação</InputLabel>
                <Select
                  value={selectedAction}
                  label="Ação"
                  onChange={(e) => setSelectedAction(e.target.value)}
                >
                  {selectedIntegration && availableActions[selectedIntegration]?.map((action) => (
                    <MenuItem key={action} value={action}>
                      {action}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={4}>
              <Button
                variant="contained"
                onClick={executeAutomation}
                disabled={executeLoading || !selectedIntegration || !selectedAction}
                startIcon={executeLoading ? <CircularProgress size={20} /> : <PlayIcon />}
                fullWidth
                size="large"
              >
                {executeLoading ? 'Executando...' : 'Executar'}
              </Button>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Parâmetros (JSON)"
                multiline
                rows={4}
                value={parameters}
                onChange={(e) => setParameters(e.target.value)}
                placeholder='{"key": "value"}'
                variant="outlined"
              />
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Status das Integrações */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Status das Integrações
          </Typography>
          
          <Grid container spacing={2}>
            {integrations.map((integration) => (
              <Grid item xs={12} sm={6} md={4} lg={3} key={integration.name}>
                <Paper 
                  sx={{ 
                    p: 2, 
                    textAlign: 'center',
                    bgcolor: integration.enabled ? 'success.light' : 'grey.200',
                    color: integration.enabled ? 'success.contrastText' : 'text.secondary'
                  }}
                >
                  <Typography variant="h6">
                    {integration.name.toUpperCase()}
                  </Typography>
                  <Typography variant="body2">
                    {integration.enabled ? 'Ativo' : 'Inativo'}
                  </Typography>
                  {integration.configured && (
                    <Chip 
                      label="Configurado" 
                      size="small" 
                      color="primary" 
                      sx={{ mt: 1 }}
                    />
                  )}
                </Paper>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Logs de Automação */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Logs de Automação
            </Typography>
            <Button
              startIcon={<RefreshIcon />}
              onClick={fetchLogs}
              disabled={loading}
            >
              Atualizar
            </Button>
          </Box>

          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Data/Hora</TableCell>
                  <TableCell>Integração</TableCell>
                  <TableCell>Ação</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Tempo (s)</TableCell>
                  <TableCell>Ações</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      <CircularProgress />
                    </TableCell>
                  </TableRow>
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      Nenhum log encontrado
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell>
                        {format(new Date(log.created_at), 'dd/MM/yyyy HH:mm:ss', { locale: ptBR })}
                      </TableCell>
                      <TableCell>
                        <Chip label={log.integration.toUpperCase()} size="small" />
                      </TableCell>
                      <TableCell>{log.action}</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={1}>
                          {getStatusIcon(log.status)}
                          {getStatusChip(log.status)}
                        </Box>
                      </TableCell>
                      <TableCell>
                        {log.execution_time ? log.execution_time.toFixed(2) : '-'}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="Ver detalhes">
                          <IconButton size="small">
                            <InfoIcon />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>

          <TablePagination
            component="div"
            count={-1} // Unknown count
            page={page}
            onPageChange={(e, newPage) => setPage(newPage)}
            rowsPerPage={rowsPerPage}
            onRowsPerPageChange={(e) => {
              setRowsPerPage(parseInt(e.target.value, 10));
              setPage(0);
            }}
            labelRowsPerPage="Logs por página:"
          />
        </CardContent>
      </Card>

      {/* Snackbar para notificações */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert 
          onClose={() => setSnackbar({ ...snackbar, open: false })} 
          severity={snackbar.severity}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

// Componente de Chat com IA
const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState([]);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const response = await api.get('/api/ai/memory');
      setConversations(response.data.conversations || []);
    } catch (error) {
      console.error('Erro ao carregar conversas:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);

    try {
      const response = await api.post('/api/ai/chat', {
        message: inputMessage,
        context: {}
      });

      const aiMessage = {
        id: Date.now() + 1,
        text: response.data.response || 'Desculpe, não consegui processar sua mensagem.',
        sender: 'ai',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Erro no chat:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sistema de IA temporariamente indisponível. Tente novamente mais tarde.',
        sender: 'ai',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Chat com IA
      </Typography>

      <Grid container spacing={3}>
        {/* Área de Chat */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '70vh', display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
              {/* Mensagens */}
              <Box 
                sx={{ 
                  flex: 1, 
                  overflowY: 'auto', 
                  mb: 2,
                  p: 1,
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1
                }}
              >
                {messages.length === 0 ? (
                  <Box 
                    display="flex" 
                    alignItems="center" 
                    justifyContent="center" 
                    height="100%"
                    color="text.secondary"
                  >
                    <Typography>
                      👋 Olá! Sou a IA do AUTOBOT. Como posso ajudá-lo hoje?
                    </Typography>
                  </Box>
                ) : (
                  messages.map((message) => (
                    <Box
                      key={message.id}
                      sx={{
                        display: 'flex',
                        justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
                        mb: 2
                      }}
                    >
                      <Paper
                        sx={{
                          p: 2,
                          maxWidth: '70%',
                          bgcolor: message.sender === 'user' ? 'primary.main' : 
                                  message.isError ? 'error.light' : 'grey.100',
                          color: message.sender === 'user' ? 'primary.contrastText' : 'text.primary'
                        }}
                      >
                        <Typography variant="body1">
                          {message.text}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            opacity: 0.7,
                            display: 'block',
                            mt: 0.5
                          }}
                        >
                          {format(message.timestamp, 'HH:mm', { locale: ptBR })}
                        </Typography>
                      </Paper>
                    </Box>
                  ))
                )}
                
                {loading && (
                  <Box display="flex" justifyContent="flex-start" mb={2}>
                    <Paper sx={{ p: 2, bgcolor: 'grey.100' }}>
                      <CircularProgress size={20} />
                      <Typography variant="body2" sx={{ ml: 1, display: 'inline' }}>
                        IA está digitando...
                      </Typography>
                    </Paper>
                  </Box>
                )}
              </Box>

              {/* Input de Mensagem */}
              <Box display="flex" gap={1}>
                <TextField
                  fullWidth
                  multiline
                  maxRows={3}
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Digite sua mensagem..."
                  disabled={loading}
                  variant="outlined"
                />
                <Button
                  variant="contained"
                  onClick={sendMessage}
                  disabled={loading || !inputMessage.trim()}
                  sx={{ minWidth: 'auto', px: 3 }}
                >
                  {loading ? <CircularProgress size={20} /> : 'Enviar'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Histórico de Conversas */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '70vh' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Histórico de Conversas
              </Typography>
              
              <List sx={{ maxHeight: '60vh', overflowY: 'auto' }}>
                {conversations.length === 0 ? (
                  <ListItem>
                    <ListItemText
                      primary="Nenhuma conversa anterior"
                      secondary="Inicie uma conversa para ver o histórico"
                    />
                  </ListItem>
                ) : (
                  conversations.map((conversation, index) => (
                    <ListItem key={index} button>
                      <ListItemIcon>
                        <ChatIcon />
                      </ListItemIcon>
                      <ListItemText
                        primary={conversation.title || `Conversa ${index + 1}`}
                        secondary={format(new Date(conversation.timestamp), 'dd/MM/yyyy HH:mm', { locale: ptBR })}
                      />
                    </ListItem>
                  ))
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

// Componente de Configurações
const Settings = () => {
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newSetting, setNewSetting] = useState({ key: '', value: '', description: '' });
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await api.get('/api/config/settings');
      setSettings(response.data.settings);
    } catch (error) {
      console.error('Erro ao carregar configurações:', error);
    } finally {
      setLoading(false);
    }
  };

  const saveSetting = async () => {
    try {
      await api.post('/api/config/settings', newSetting);
      setDialogOpen(false);
      setNewSetting({ key: '', value: '', description: '' });
      fetchSettings();
    } catch (error) {
      console.error('Erro ao salvar configuração:', error);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Configurações
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setDialogOpen(true)}
        >
          Nova Configuração
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Configurações do Sistema */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configurações do Sistema
              </Typography>
              
              {loading ? (
                <CircularProgress />
              ) : (
                <List>
                  {settings.map((setting, index) => (
                    <React.Fragment key={setting.key}>
                      <ListItem>
                        <ListItemText
                          primary={setting.key}
                          secondary={setting.description || 'Sem descrição'}
                        />
                        <Typography variant="body2" color="primary">
                          {setting.value}
                        </Typography>
                      </ListItem>
                      {index < settings.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Configurações de IA */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Configurações de IA
              </Typography>
              
              <List>
                <ListItem>
                  <ListItemText
                    primary="Modelo Ativo"
                    secondary="Modelo de IA atualmente em uso"
                  />
                  <Chip label="llama3.1" color="primary" />
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Temperatura"
                    secondary="Criatividade das respostas (0.0 - 1.0)"
                  />
                  <Typography variant="body2">0.7</Typography>
                </ListItem>
                <Divider />
                <ListItem>
                  <ListItemText
                    primary="Contexto Máximo"
                    secondary="Tokens máximos por conversa"
                  />
                  <Typography variant="body2">4096</Typography>
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Dialog para nova configuração */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nova Configuração</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Chave"
            value={newSetting.key}
            onChange={(e) => setNewSetting({ ...newSetting, key: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Valor"
            value={newSetting.value}
            onChange={(e) => setNewSetting({ ...newSetting, value: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Descrição"
            value={newSetting.description}
            onChange={(e) => setNewSetting({ ...newSetting, description: e.target.value })}
            margin="normal"
            multiline
            rows={2}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cancelar
          </Button>
          <Button onClick={saveSetting} variant="contained">
            Salvar
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

// Layout Principal
const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
    { text: 'Automações', icon: <IntegrationIcon />, path: '/automations' },
    { text: 'Chat IA', icon: <ChatIcon />, path: '/ai-chat' },
    { text: 'Configurações', icon: <SettingsIcon />, path: '/settings' }
  ];

  const handleLogout = () => {
    logout();
    setAnchorEl(null);
  };

  return (
    <Box sx={{ display: 'flex' }}>
      {/* App Bar */}
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={() => setDrawerOpen(!drawerOpen)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            🤖 AUTOBOT - IA Local Corporativa
          </Typography>

          <Box display="flex" alignItems="center" gap={1}>
            <IconButton color="inherit">
              <Badge badgeContent={4} color="error">
                <NotificationsIcon />
              </Badge>
            </IconButton>
            
            <IconButton
              color="inherit"
              onClick={(e) => setAnchorEl(e.currentTarget)}
            >
              <Avatar sx={{ width: 32, height: 32 }}>
                {user?.username?.charAt(0).toUpperCase()}
              </Avatar>
            </IconButton>

            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={() => setAnchorEl(null)}
            >
              <MenuItem onClick={() => setAnchorEl(null)}>
                <AccountIcon sx={{ mr: 1 }} />
                Perfil
              </MenuItem>
              <MenuItem onClick={handleLogout}>
                <LogoutIcon sx={{ mr: 1 }} />
                Logout
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      {/* Drawer */}
      <Drawer
        variant="persistent"
        anchor="left"
        open={drawerOpen}
        sx={{
          width: 240,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: 240,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem
                key={item.text}
                button
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>
                  {item.icon}
                </ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Conteúdo Principal */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 0,
          transition: 'margin 225ms cubic-bezier(0.4, 0, 0.6, 1) 0ms',
          marginLeft: drawerOpen ? '240px' : 0,
          minHeight: '100vh',
          bgcolor: 'background.default'
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
};

// Componente de Rota Protegida
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Componente Principal da Aplicação
const App = () => {
  return (
    <ThemeProvider theme={theme}>
      <AuthProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<LoginForm />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/automations" element={
              <ProtectedRoute>
                <Automations />
              </ProtectedRoute>
            } />
            <Route path="/ai-chat" element={
              <ProtectedRoute>
                <AIChat />
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;
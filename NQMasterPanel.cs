// NQMaster panel window (2026-10-23, Federico: "opción 2"). A WPF window, separate from the chart, that shows every running NQMaster
// instance (one per account / instrument) with tabs Resumen / Cuenta / Módulos / Avisos. The strategy only publishes an immutable
// snapshot (NQMasterUI.Snapshot) to a static hub every bar; the window polls the hub once a second on the UI thread. Nothing here
// can place or change an order, and every UI call is wrapped so a drawing error never reaches the strategy.
// Copy this file next to NQMaster.cs (Documents\NinjaTrader 8\bin\Custom\Strategies) and press F5.
#region Using declarations
using System;
using System.Collections.Generic;
using System.Globalization;
using W = System.Windows;
using C = System.Windows.Controls;
using M = System.Windows.Media;
using Sh = System.Windows.Shapes;
using T = System.Windows.Threading;
#endregion

namespace NQMasterUI
{
	public class ModuleRow { public string Name; public bool On; public string State; public int Trades, Trades365; public double Wr, Pf, Net, Wr365, Pf365, Net365; }
	public class EventRow { public DateTime Day; public string Text; public int Kind; }		// Kind: 0 info, 1 good (pass / payout), -1 bad (lost)

	// everything the window shows; built by the strategy, never modified after Publish
	public class Snapshot
	{
		public string Key, Title, Mode, Status, Profile, Instrument, Account;
		public DateTime Time;
		public string Trend; public double Atr; public bool Pullback;
		public int Trades; public double WinRate, Pf, Net, PerTrade, PerMonth, MaxDd, BestDay, WorstDay, GreenPct, Commission; public DateTime First;
		public List<DateTime> EqDays = new List<DateTime>(); public List<double> EqVals = new List<double>();
		public bool Live; public int LiveDays, LiveTrades; public double LivePnl, LiveExpected;
		public bool EdgeOn; public double EdgePct; public int EdgeDays; public string EdgeState = "";
		public List<ModuleRow> Modules = new List<ModuleRow>();
		// account simulation
		public bool SimOn; public bool SimFrozen; public string Firm = "", SimPhase = "", SimNext = "", SimStatus = "";
		public int Evals, EvalPass, EvalLost, Funded, FundedLost, FundedDone, Payouts, SimNumber, SimDay;
		public double PayGross, PayCash, Fees, SimNet, SimPerMonth, SimMonths, SimProfit, SimTarget, SimBalance, SimLimit, SimCushion, SimDd;
		public List<EventRow> Events = new List<EventRow>();
		public List<DateTime> CashDays = new List<DateTime>(); public List<double> CashVals = new List<double>();
		// real prop account (live)
		public bool RealOn; public string RealName = "", RealPhase = "", RealPayout = ""; public double RealBalance, RealProfit, RealLimit, RealCushion, RealToday, RealTarget, RealDd;
		public List<string> Warnings = new List<string>();
	}

	public static class Hub
	{
		private static readonly object Sync = new object();
		private static readonly Dictionary<string, Snapshot> Snaps = new Dictionary<string, Snapshot>();
		private static int version;
		private static PanelWindow window;
		public static void Publish(Snapshot s) { if (s == null || s.Key == null) return; lock (Sync) { Snaps[s.Key] = s; version++; } }
		public static void Remove(string key) { if (key == null) return; lock (Sync) { if (Snaps.Remove(key)) version++; } }
		public static int Version { get { lock (Sync) return version; } }
		public static List<Snapshot> All() { lock (Sync) return new List<Snapshot>(Snaps.Values); }
		// called from the strategy thread: open (or bring forward) the single window on the UI thread
		public static void Open()
		{
			try
			{
				if (W.Application.Current == null) return;
				W.Application.Current.Dispatcher.InvokeAsync(new Action(OpenOnUi));
			}
			catch { }
		}
		private static void OpenOnUi()
		{
			try
			{
				if (window == null) { window = new PanelWindow(); window.Closed += (s, e) => { window = null; }; window.Show(); }
				else { if (window.WindowState == W.WindowState.Minimized) window.WindowState = W.WindowState.Normal; window.Activate(); }
			}
			catch { window = null; }
		}
	}

	public class PanelWindow : W.Window
	{
		// palette (dark, like NinjaTrader's default skin)
		private static readonly M.Brush Bg = B(0x16, 0x18, 0x1D), Card = B(0x22, 0x26, 0x2E), Line = B(0x33, 0x39, 0x44), Text = B(0xE6, 0xE8, 0xEB),
			Dim = B(0x98, 0xA1, 0xAE), Green = B(0x3F, 0xB9, 0x50), Red = B(0xF8, 0x51, 0x49), Amber = B(0xD2, 0x99, 0x22), Blue = B(0x58, 0xA6, 0xFF);
		private static readonly CultureInfo Inv = CultureInfo.InvariantCulture;
		private readonly C.ComboBox picker = new C.ComboBox();
		private readonly C.TabControl tabs = new C.TabControl();
		private readonly T.DispatcherTimer timer = new T.DispatcherTimer();
		private int shownVersion = -1; private List<string> keys = new List<string>();

		public PanelWindow()
		{
			Title = "NQMaster"; Width = 980; Height = 760; Background = Bg; Foreground = Text;
			C.DockPanel root = new C.DockPanel();
			C.Border top = new C.Border(); top.Background = Card; top.Padding = new W.Thickness(12, 8, 12, 8); top.BorderBrush = Line; top.BorderThickness = new W.Thickness(0, 0, 0, 1);
			C.StackPanel tp = new C.StackPanel(); tp.Orientation = C.Orientation.Horizontal;
			tp.Children.Add(Txt("NQMASTER", 18, Text, true));
			C.TextBlock lab = Txt("   Cuenta:", 13, Dim, false); lab.VerticalAlignment = W.VerticalAlignment.Center; tp.Children.Add(lab);
			picker.MinWidth = 420; picker.Margin = new W.Thickness(8, 0, 0, 0); picker.SelectionChanged += (s, e) => { shownVersion = -1; Refresh(); };
			tp.Children.Add(picker);
			top.Child = tp; C.DockPanel.SetDock(top, C.Dock.Top); root.Children.Add(top);
			tabs.Background = Bg; tabs.BorderThickness = new W.Thickness(0); tabs.Margin = new W.Thickness(6);
			root.Children.Add(tabs);
			Content = root;
			timer.Interval = TimeSpan.FromSeconds(1); timer.Tick += (s, e) => Refresh(); timer.Start();
			Closed += (s, e) => { try { timer.Stop(); } catch { } };
			Refresh();
		}

		// ---------------------------------------------------------------- refresh
		private void Refresh()
		{
			try
			{
				int v = Hub.Version; if (v == shownVersion) return; shownVersion = v;
				List<Snapshot> all = Hub.All(); all.Sort((a, b) => string.Compare(a.Title, b.Title, StringComparison.Ordinal));
				List<string> nk = new List<string>(); foreach (Snapshot s in all) nk.Add(s.Key);
				string sel = picker.SelectedIndex >= 0 && picker.SelectedIndex < keys.Count ? keys[picker.SelectedIndex] : null;
				if (!SameKeys(nk, keys))
				{
					keys = nk; picker.Items.Clear(); foreach (Snapshot s in all) picker.Items.Add(s.Title);
					int i = sel != null ? keys.IndexOf(sel) : -1; picker.SelectedIndex = i >= 0 ? i : (keys.Count > 0 ? 0 : -1);
					return;		// SelectionChanged calls Refresh again
				}
				int k = picker.SelectedIndex; Snapshot snap = k >= 0 && k < all.Count ? all[k] : null;
				int tab = tabs.SelectedIndex < 0 ? 0 : tabs.SelectedIndex; double off = 0;
				try { C.TabItem cur = tabs.SelectedItem as C.TabItem; C.ScrollViewer sv = cur != null ? cur.Content as C.ScrollViewer : null; if (sv != null) off = sv.VerticalOffset; } catch { }
				tabs.Items.Clear();
				if (snap == null) { tabs.Items.Add(Tab("NQMaster", Scroll(Pad(Txt("No hay ninguna estrategia NQMaster activa. Activala en un gráfico (pasa a vivo) o apretá Ctrl+Shift+P en el gráfico.", 14, Dim, false))))); return; }
				tabs.Items.Add(Tab("Resumen", Scroll(Summary(snap))));
				tabs.Items.Add(Tab("Cuenta", Scroll(AccountTab(snap))));
				tabs.Items.Add(Tab("Módulos", Scroll(ModulesTab(snap))));
				tabs.Items.Add(Tab(snap.Warnings.Count > 0 ? "Avisos (" + snap.Warnings.Count + ")" : "Avisos", Scroll(WarningsTab(snap))));
				tabs.SelectedIndex = Math.Min(tab, tabs.Items.Count - 1);
				try { C.TabItem now = tabs.SelectedItem as C.TabItem; C.ScrollViewer sv2 = now != null ? now.Content as C.ScrollViewer : null; if (sv2 != null && off > 0) sv2.ScrollToVerticalOffset(off); } catch { }
			}
			catch (Exception ex) { try { tabs.Items.Clear(); tabs.Items.Add(Tab("Error", Pad(Txt("Error del panel (la estrategia sigue operando): " + ex.Message, 13, Red, false)))); } catch { } }
		}
		private static bool SameKeys(List<string> a, List<string> b) { if (a.Count != b.Count) return false; for (int i = 0; i < a.Count; i++) if (a[i] != b[i]) return false; return true; }

		// ---------------------------------------------------------------- tabs
		private W.UIElement Summary(Snapshot s)
		{
			C.StackPanel p = Stack();
			p.Children.Add(Header(s));
			C.WrapPanel kpi = new C.WrapPanel();
			kpi.Children.Add(Kpi("Neto", Usd(s.Net), s.Net >= 0 ? Green : Red, s.Trades > 0 ? s.Trades + " trades" : "sin trades"));
			kpi.Children.Add(Kpi("Por mes", Usd(s.PerMonth), s.PerMonth >= 0 ? Green : Red, "desde " + D(s.First)));
			kpi.Children.Add(Kpi("Ganadoras", Pct(s.WinRate), Text, "factor de beneficio " + (s.Pf > 0 ? Dec(s.Pf) : "-")));
			kpi.Children.Add(Kpi("Caída máxima", Usd(-s.MaxDd), Red, "peor día " + Usd(s.WorstDay)));
			kpi.Children.Add(Kpi("Días positivos", Pct(s.GreenPct), Text, "mejor día " + Usd(s.BestDay)));
			kpi.Children.Add(Kpi("Por trade", Usd(s.PerTrade), s.PerTrade >= 0 ? Green : Red, s.Commission > 0.005 ? "comisiones incluidas" : "SIN comisiones"));
			p.Children.Add(kpi);
			p.Children.Add(CardOf("Curva de ganancia (cierre de cada día)", Curve(s.EqVals, s.Net >= 0 ? Green : Red, 860, 200)));
			if (s.Live)
			{
				string verdict = s.LiveDays < 40 ? "menos de 40 sesiones: todavía es ruido" : (s.LivePnl >= 0.5 * s.LiveExpected ? "rinde" : "rinde POR DEBAJO de lo esperado");
				p.Children.Add(CardOf("En vivo", Rows(new string[,] { { "Sesiones", s.LiveDays.ToString() }, { "Trades", s.LiveTrades.ToString() },
					{ "Resultado", Usd(s.LivePnl) }, { "Esperado por el backtest", Usd(s.LiveExpected) }, { "Lectura", verdict } })));
			}
			if (s.EdgeOn)
			{
				C.StackPanel e = Stack();
				e.Children.Add(Bar(Math.Min(100, s.EdgePct), 100, s.EdgeState == "ALARMA" ? Red : (s.EdgeState == "AVISO" ? Amber : Green)));
				e.Children.Add(Txt(string.Format("{0} de la alarma  ·  {1} días  ·  {2}", Pct(s.EdgePct), s.EdgeDays, s.EdgeState), 13, Dim, false));
				p.Children.Add(CardOf("Monitor de borde", e));
			}
			return p;
		}

		private W.UIElement AccountTab(Snapshot s)
		{
			C.StackPanel p = Stack();
			if (s.RealOn)
			{
				C.StackPanel r = Stack();
				r.Children.Add(Rows(new string[,] { { "Cuenta", s.RealName }, { "Fase", s.RealPhase }, { "Saldo", Usd(s.RealBalance) + "  (" + Usd(s.RealProfit) + ")" },
					{ "Límite de pérdida", Usd(s.RealLimit) }, { "Colchón", Usd(s.RealCushion) }, { "Hoy", Usd(s.RealToday) } }));
				r.Children.Add(Txt("Colchón hasta el límite", 12, Dim, false)); r.Children.Add(Bar(Math.Max(0, s.RealCushion), Math.Max(1, s.RealDd), s.RealCushion < 0.25 * s.RealDd ? Red : (s.RealCushion < 0.5 * s.RealDd ? Amber : Green)));
				if (s.RealTarget > 0) { r.Children.Add(Txt("Objetivo de la evaluación", 12, Dim, false)); r.Children.Add(Bar(Math.Max(0, s.RealProfit), s.RealTarget, Blue)); }
				if (s.RealPayout.Length > 0) r.Children.Add(Txt("Retiro: " + s.RealPayout, 13, s.RealPayout.StartsWith("DISPONIBLE") ? Green : Text, false));
				p.Children.Add(CardOf("CUENTA REAL", r));
			}
			if (!s.SimOn) { p.Children.Add(CardOf("Simulación de cuenta", Txt(s.SimStatus.Length > 0 ? s.SimStatus : "Elegí un preset de firma y la fase (Eval / Funded) para simular retiros y cuentas perdidas.", 13, Dim, false))); return p; }
			p.Children.Add(Txt(string.Format("SIMULACIÓN  ·  {0}{1}", s.Firm, s.SimFrozen ? "  ·  backtest (congelada al pasar a vivo)" : ""), 15, Text, true));
			p.Children.Add(Txt("Regla: si se pierde una cuenta, al día siguiente se compra otra evaluación.", 12, Dim, false));
			C.WrapPanel kpi = new C.WrapPanel();
			kpi.Children.Add(Kpi("Resultado neto", Usd(s.SimNet), s.SimNet >= 0 ? Green : Red, Usd(s.SimPerMonth) + " por mes  ·  " + Dec1(s.SimMonths) + " meses"));
			kpi.Children.Add(Kpi("Retiros", s.Payouts.ToString(), Green, "cobrado " + Usd(s.PayCash) + " (pedido " + Usd(s.PayGross) + ")"));
			kpi.Children.Add(Kpi("Evaluaciones", s.Evals.ToString(), Text, s.EvalPass + " aprobadas  ·  " + s.EvalLost + " perdidas"));
			kpi.Children.Add(Kpi("Fondeadas", s.Funded.ToString(), Text, s.FundedLost + " perdidas  ·  " + s.FundedDone + " completadas"));
			kpi.Children.Add(Kpi("Costos", Usd(-s.Fees), Red, "evaluaciones y activaciones"));
			p.Children.Add(kpi);
			if (s.CashVals.Count > 1) p.Children.Add(CardOf("Cobrado neto acumulado (retiros − costos)", Curve(s.CashVals, s.SimNet >= 0 ? Green : Red, 860, 150)));
			if (!s.SimFrozen && s.SimPhase.Length > 0)
			{
				C.StackPanel c = Stack();
				c.Children.Add(Txt(string.Format("{0} #{1}  ·  día {2}", s.SimPhase, s.SimNumber, s.SimDay), 14, Text, true));
				c.Children.Add(Rows(new string[,] { { "Ganancia", Usd(s.SimProfit) }, { "Saldo", Usd(s.SimBalance) }, { "Límite de pérdida", Usd(s.SimLimit) }, { "Colchón", Usd(s.SimCushion) } }));
				c.Children.Add(Txt("Colchón hasta el límite", 12, Dim, false)); c.Children.Add(Bar(Math.Max(0, s.SimCushion), Math.Max(1, s.SimDd), s.SimCushion < 0.25 * s.SimDd ? Red : (s.SimCushion < 0.5 * s.SimDd ? Amber : Green)));
				if (s.SimPhase.StartsWith("EVAL") && s.SimTarget > 0) { c.Children.Add(Txt("Objetivo", 12, Dim, false)); c.Children.Add(Bar(Math.Max(0, s.SimProfit), s.SimTarget, Blue)); }
				if (s.SimNext.Length > 0) c.Children.Add(Txt("Próximo retiro: " + s.SimNext, 13, Text, false));
				p.Children.Add(CardOf("Cuenta actual", c));
			}
			else if (s.SimStatus.Length > 0) p.Children.Add(CardOf("Cuenta actual", Txt(s.SimStatus, 13, Dim, false)));
			C.StackPanel ev = Stack();
			for (int i = s.Events.Count - 1; i >= 0; i--)
			{
				EventRow e = s.Events[i];
				ev.Children.Add(Txt(D(e.Day) + "   " + e.Text, 13, e.Kind > 0 ? Green : (e.Kind < 0 ? Red : Text), false));
			}
			if (s.Events.Count == 0) ev.Children.Add(Txt("Sin eventos todavía.", 13, Dim, false));
			p.Children.Add(CardOf("Historial (más reciente arriba)", ev));
			return p;
		}

		private W.UIElement ModulesTab(Snapshot s)
		{
			C.StackPanel p = Stack();
			p.Children.Add(Txt("Por módulo: todo el período cargado y los últimos 365 días. Para la revisión anual, no para cambiar el tamaño.", 12, Dim, false));
			C.Grid g = new C.Grid(); g.Margin = new W.Thickness(0, 8, 0, 0);
			string[] head = { "Módulo", "Estado", "Trades", "Ganadoras", "PF", "Neto", "Trades 365d", "Ganadoras 365d", "PF 365d", "Neto 365d" };
			for (int c = 0; c < head.Length; c++) g.ColumnDefinitions.Add(new C.ColumnDefinition { Width = new W.GridLength(c == 0 ? 1.2 : 1, W.GridUnitType.Star) });
			g.RowDefinitions.Add(new C.RowDefinition { Height = W.GridLength.Auto });
			for (int c = 0; c < head.Length; c++) Cell(g, 0, c, Txt(head[c], 12, Dim, true));
			int r = 1;
			foreach (ModuleRow m in s.Modules)
			{
				g.RowDefinitions.Add(new C.RowDefinition { Height = W.GridLength.Auto });
				M.Brush net = m.Net >= 0 ? Green : Red, net365 = m.Trades365 == 0 ? Dim : (m.Net365 >= 0 ? Green : Red);
				Cell(g, r, 0, Txt(m.Name, 13, m.On ? Text : Dim, true));
				Cell(g, r, 1, Txt(m.On ? (m.State.Length > 0 ? m.State : "activo") : "apagado", 12, m.State == "en posición" ? Blue : (m.On ? Text : Dim), false));
				Cell(g, r, 2, Txt(m.Trades.ToString(), 13, Text, false));
				Cell(g, r, 3, Txt(m.Trades > 0 ? Pct(m.Wr) : "-", 13, Text, false));
				Cell(g, r, 4, Txt(m.Trades > 0 ? (m.Pf > 0 ? Dec(m.Pf) : "sin pérd.") : "-", 13, m.Trades > 0 && m.Pf > 0 && m.Pf < 1 ? Red : Text, false));
				Cell(g, r, 5, Txt(m.Trades > 0 ? Usd(m.Net) : "-", 13, net, false));
				Cell(g, r, 6, Txt(m.Trades365.ToString(), 13, Text, false));
				Cell(g, r, 7, Txt(m.Trades365 > 0 ? Pct(m.Wr365) : "-", 13, Text, false));
				Cell(g, r, 8, Txt(m.Trades365 > 0 ? (m.Pf365 > 0 ? Dec(m.Pf365) : "sin pérd.") : "-", 13, m.Trades365 >= 20 && m.Pf365 > 0 && m.Pf365 < 1 ? Red : Text, false));
				Cell(g, r, 9, Txt(m.Trades365 > 0 ? Usd(m.Net365) : "-", 13, net365, false));
				r++;
			}
			p.Children.Add(CardOf("Módulos", g));
			return p;
		}

		private W.UIElement WarningsTab(Snapshot s)
		{
			C.StackPanel p = Stack();
			if (s.Warnings.Count == 0) p.Children.Add(CardOf("Avisos", Txt("Sin avisos.", 13, Green, false)));
			else { C.StackPanel w = Stack(); foreach (string x in s.Warnings) w.Children.Add(Txt("•  " + x, 13, Amber, false)); p.Children.Add(CardOf("Avisos", w)); }
			p.Children.Add(CardOf("Datos", Rows(new string[,] { { "Instrumento", s.Instrument }, { "Cuenta", s.Account }, { "Perfil", s.Profile }, { "Modo", s.Mode },
				{ "Última barra", s.Time.ToString("dd-MM-yy HH:mm", Inv) }, { "Comisiones del período", Usd(s.Commission) } })));
			return p;
		}

		private W.UIElement Header(Snapshot s)
		{
			C.Border b = CardBorder();
			C.StackPanel p = Stack();
			C.StackPanel l1 = new C.StackPanel(); l1.Orientation = C.Orientation.Horizontal;
			l1.Children.Add(Txt(s.Profile + "  ·  " + s.Instrument + "  ·  " + s.Account, 15, Text, true));
			C.Border pill = new C.Border(); pill.CornerRadius = new W.CornerRadius(9); pill.Padding = new W.Thickness(8, 1, 8, 1); pill.Margin = new W.Thickness(12, 0, 0, 0);
			pill.Background = s.Mode.StartsWith("EN VIVO") ? Green : Blue; pill.Child = Txt(s.Mode, 12, Bg, true); l1.Children.Add(pill);
			p.Children.Add(l1);
			p.Children.Add(Txt("Estado: " + s.Status, 13, s.Status == "operando" ? Green : Amber, false));
			p.Children.Add(Txt(string.Format("Tendencia {0}  ·  ATR diario {1}  ·  día de pullback: {2}", s.Trend, s.Atr > 0 ? s.Atr.ToString("0", Inv) : "-", s.Pullback ? "sí" : "no"), 13, Dim, false));
			b.Child = p; return b;
		}

		// ---------------------------------------------------------------- building blocks
		private static M.SolidColorBrush B(byte r, byte g, byte b) { M.SolidColorBrush x = new M.SolidColorBrush(M.Color.FromRgb(r, g, b)); x.Freeze(); return x; }
		private static C.TextBlock Txt(string s, double size, M.Brush fg, bool bold)
		{
			C.TextBlock t = new C.TextBlock(); t.Text = s ?? ""; t.FontSize = size; t.Foreground = fg; t.TextWrapping = W.TextWrapping.Wrap;
			if (bold) t.FontWeight = W.FontWeights.SemiBold; t.Margin = new W.Thickness(0, 2, 0, 2); return t;
		}
		private static C.StackPanel Stack() { C.StackPanel p = new C.StackPanel(); p.Orientation = C.Orientation.Vertical; return p; }
		private static C.Border Pad(W.UIElement e) { C.Border b = new C.Border(); b.Padding = new W.Thickness(16); b.Child = e; return b; }
		private static C.ScrollViewer Scroll(W.UIElement e) { C.ScrollViewer s = new C.ScrollViewer(); s.VerticalScrollBarVisibility = C.ScrollBarVisibility.Auto; s.Content = Pad(e); return s; }
		private static C.TabItem Tab(string header, object content) { C.TabItem t = new C.TabItem(); t.Header = header; t.Content = content; return t; }
		private static C.Border CardBorder()
		{
			C.Border b = new C.Border(); b.Background = Card; b.BorderBrush = Line; b.BorderThickness = new W.Thickness(1); b.CornerRadius = new W.CornerRadius(8);
			b.Padding = new W.Thickness(14, 10, 14, 10); b.Margin = new W.Thickness(0, 0, 0, 10); return b;
		}
		private static C.Border CardOf(string title, W.UIElement body)
		{
			C.Border b = CardBorder(); C.StackPanel p = Stack();
			p.Children.Add(Txt(title, 12, Dim, true)); p.Children.Add(body); b.Child = p; return b;
		}
		private static C.Border Kpi(string label, string value, M.Brush color, string sub)
		{
			C.Border b = CardBorder(); b.Width = 200; b.Margin = new W.Thickness(0, 0, 10, 10);
			C.StackPanel p = Stack(); p.Children.Add(Txt(label, 12, Dim, false)); p.Children.Add(Txt(value, 22, color, true)); p.Children.Add(Txt(sub, 11, Dim, false));
			b.Child = p; return b;
		}
		private static C.ProgressBar Bar(double v, double max, M.Brush color)
		{
			C.ProgressBar pb = new C.ProgressBar(); pb.Minimum = 0; pb.Maximum = Math.Max(1e-9, max); pb.Value = Math.Max(0, Math.Min(v, pb.Maximum));
			pb.Height = 10; pb.Foreground = color; pb.Background = Line; pb.BorderThickness = new W.Thickness(0); pb.Margin = new W.Thickness(0, 2, 0, 6); return pb;
		}
		private static C.Grid Rows(string[,] kv)
		{
			C.Grid g = new C.Grid();
			g.ColumnDefinitions.Add(new C.ColumnDefinition { Width = new W.GridLength(200) }); g.ColumnDefinitions.Add(new C.ColumnDefinition { Width = new W.GridLength(1, W.GridUnitType.Star) });
			for (int i = 0; i < kv.GetLength(0); i++)
			{
				g.RowDefinitions.Add(new C.RowDefinition { Height = W.GridLength.Auto });
				Cell(g, i, 0, Txt(kv[i, 0], 13, Dim, false)); Cell(g, i, 1, Txt(kv[i, 1], 13, Text, false));
			}
			return g;
		}
		private static void Cell(C.Grid g, int r, int c, W.UIElement e) { C.Grid.SetRow(e, r); C.Grid.SetColumn(e, c); g.Children.Add(e); }
		// line chart in a fixed logical box, stretched to the card width; zero line in grey
		private static W.UIElement Curve(List<double> v, M.Brush color, double w, double h)
		{
			if (v == null || v.Count < 2) return Txt("Todavía no hay suficientes días.", 13, Dim, false);
			double lo = 0, hi = 0; foreach (double x in v) { if (x < lo) lo = x; if (x > hi) hi = x; }
			if (hi - lo < 1) hi = lo + 1;
			C.Canvas cv = new C.Canvas(); cv.Width = w; cv.Height = h;
			Sh.Polyline pl = new Sh.Polyline(); pl.Stroke = color; pl.StrokeThickness = 2;
			M.PointCollection pts = new M.PointCollection();
			for (int i = 0; i < v.Count; i++) pts.Add(new W.Point(w * i / (v.Count - 1), h - h * (v[i] - lo) / (hi - lo)));
			pl.Points = pts;
			Sh.Line zero = new Sh.Line(); zero.X1 = 0; zero.X2 = w; zero.Y1 = zero.Y2 = h - h * (0 - lo) / (hi - lo); zero.Stroke = Line; zero.StrokeThickness = 1;
			cv.Children.Add(zero); cv.Children.Add(pl);
			C.Viewbox vb = new C.Viewbox(); vb.Stretch = M.Stretch.Fill; vb.Height = h; vb.Child = cv;
			C.StackPanel p = Stack(); p.Children.Add(vb);
			p.Children.Add(Txt(string.Format("máximo {0}  ·  mínimo {1}  ·  último {2}", Usd(hi), Usd(lo), Usd(v[v.Count - 1])), 11, Dim, false));
			return p;
		}
		// ---------------------------------------------------------------- formats (Spanish: thousands with dots, decimals with commas)
		public static string Usd(double v) { string s = Math.Abs(v).ToString("#,0", Inv).Replace(',', '.'); return (v < -0.5 ? "-$" : "$") + s; }
		public static string Pct(double v) { return v.ToString("0.0", Inv).Replace('.', ',') + "%"; }
		public static string Dec(double v) { return v.ToString("0.00", Inv).Replace('.', ','); }
		public static string Dec1(double v) { return v.ToString("0.0", Inv).Replace('.', ','); }
		public static string D(DateTime d) { return d == DateTime.MinValue ? "-" : d.ToString("dd-MM-yy", Inv); }
	}
}

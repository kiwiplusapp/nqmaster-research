// Minimal WPF API stub for the cloud C# 5 type check (mono has no WPF). Only the members NQMaster / NQMasterPanel use; signatures
// follow the real .NET Framework 4.8 API. This is NOT a compile: the real check is F5 in NinjaTrader.
using System;
using System.Collections.Generic;
namespace System.Windows.Threading
{
	public enum DispatcherPriority { Normal }
	public class DispatcherOperation { }
	public class Dispatcher { public DispatcherOperation InvokeAsync(Action a) { return null; } public bool CheckAccess() { return true; } }
	public class DispatcherObject { public Dispatcher Dispatcher { get { return null; } } }
	public class DispatcherTimer { public TimeSpan Interval; public event EventHandler Tick; public void Start() { } public void Stop() { } }
}
namespace System.Windows
{
	public struct Thickness { public Thickness(double u) { } public Thickness(double l, double t, double r, double b) { } }
	public struct CornerRadius { public CornerRadius(double u) { } }
	public struct Point { public Point(double x, double y) { } }
	public enum GridUnitType { Auto, Pixel, Star }
	public struct GridLength { public GridLength(double v) { } public GridLength(double v, GridUnitType t) { } public static GridLength Auto { get { return new GridLength(); } } }
	public enum VerticalAlignment { Top, Center, Bottom, Stretch }
	public enum HorizontalAlignment { Left, Center, Right, Stretch }
	public enum TextWrapping { NoWrap, Wrap }
	public enum WindowState { Normal, Minimized, Maximized }
	public struct FontWeight { }
	public static class FontWeights { public static FontWeight SemiBold { get { return new FontWeight(); } } public static FontWeight Bold { get { return new FontWeight(); } } }
	public class Freezable : System.Windows.Threading.DispatcherObject { public void Freeze() { } }
	public class RoutedEvent { }
	public class UIElement : System.Windows.Threading.DispatcherObject { public event System.Windows.Input.KeyEventHandler PreviewKeyDown; public static readonly RoutedEvent PreviewKeyDownEvent = new RoutedEvent(); public void AddHandler(RoutedEvent e, Delegate h, bool handledEventsToo) { } public void RemoveHandler(RoutedEvent e, Delegate h) { } }
	public class FrameworkElement : UIElement { public object Tag; public double Width, Height, MinWidth; public Thickness Margin; public VerticalAlignment VerticalAlignment; public HorizontalAlignment HorizontalAlignment; }
	public class Window : System.Windows.Controls.ContentControl { public string Title; public WindowState WindowState; public event EventHandler Closed; public void Show() { } public void Close() { } public bool Activate() { return true; } }
	public class WindowCollection : System.Collections.IEnumerable { public System.Collections.IEnumerator GetEnumerator() { return new List<Window>().GetEnumerator(); } }
	public class Application { public static Application Current { get { return null; } } public System.Windows.Threading.Dispatcher Dispatcher { get { return null; } } public WindowCollection Windows { get { return null; } } }
}
namespace System.Windows.Input
{
	public enum Key { P }
	[Flags] public enum ModifierKeys { None = 0, Alt = 1, Control = 2, Shift = 4 }
	public static class Keyboard { public static ModifierKeys Modifiers { get { return ModifierKeys.None; } } }
	public class KeyEventArgs : EventArgs { public Key Key; public bool Handled; }
	public delegate void KeyEventHandler(object sender, KeyEventArgs e);
}
namespace System.Windows.Media
{
	public struct Color { public static Color FromRgb(byte r, byte g, byte b) { return new Color(); } }
	public class SolidColorBrush : Brush { public SolidColorBrush(Color c) { } public void Freeze() { } }
	public class PointCollection : List<System.Windows.Point> { }
	public enum Stretch { None, Fill, Uniform, UniformToFill }
}
namespace System.Windows.Shapes
{
	public class Shape : System.Windows.FrameworkElement { public System.Windows.Media.Brush Stroke; public double StrokeThickness; }
	public class Polyline : Shape { public System.Windows.Media.PointCollection Points; }
	public class Line : Shape { public double X1, X2, Y1, Y2; }
}
namespace System.Windows.Controls
{
	public class UIElementCollection : List<System.Windows.UIElement> { }
	public class ItemCollection : List<object> { }
	public class Control : System.Windows.FrameworkElement { public System.Windows.Media.Brush Background, Foreground, BorderBrush; public System.Windows.Thickness BorderThickness, Padding; }
	public class ContentControl : Control { public object Content; }
	public class Panel : System.Windows.FrameworkElement { public UIElementCollection Children = new UIElementCollection(); public System.Windows.Media.Brush Background; }
	public enum Orientation { Horizontal, Vertical }
	public enum Dock { Left, Top, Right, Bottom }
	public enum ScrollBarVisibility { Disabled, Auto, Hidden, Visible }
	public class StackPanel : Panel { public Orientation Orientation; }
	public class WrapPanel : Panel { }
	public class DockPanel : Panel { public static void SetDock(System.Windows.UIElement e, Dock d) { } }
	public class Canvas : Panel { }
	public class ColumnDefinition { public System.Windows.GridLength Width; }
	public class RowDefinition { public System.Windows.GridLength Height; }
	public class Grid : Panel
	{
		public List<ColumnDefinition> ColumnDefinitions = new List<ColumnDefinition>(); public List<RowDefinition> RowDefinitions = new List<RowDefinition>();
		public static void SetRow(System.Windows.UIElement e, int r) { } public static void SetColumn(System.Windows.UIElement e, int c) { }
	}
	public class Border : System.Windows.FrameworkElement
	{
		public System.Windows.Media.Brush Background, BorderBrush; public System.Windows.Thickness BorderThickness, Padding; public System.Windows.CornerRadius CornerRadius; public System.Windows.UIElement Child;
	}
	public class TextBlock : System.Windows.FrameworkElement
	{
		public string Text; public double FontSize; public System.Windows.Media.Brush Foreground; public System.Windows.TextWrapping TextWrapping; public System.Windows.FontWeight FontWeight;
	}
	public class Viewbox : System.Windows.FrameworkElement { public System.Windows.Media.Stretch Stretch; public System.Windows.UIElement Child; }
	public class ScrollViewer : ContentControl { public ScrollBarVisibility VerticalScrollBarVisibility, HorizontalScrollBarVisibility; public double VerticalOffset { get { return 0; } } public void ScrollToVerticalOffset(double o) { } }
	public class SelectionChangedEventArgs : EventArgs { }
	public delegate void SelectionChangedEventHandler(object sender, SelectionChangedEventArgs e);
	public class Selector : Control { public ItemCollection Items = new ItemCollection(); public int SelectedIndex; public object SelectedItem; public event SelectionChangedEventHandler SelectionChanged; }
	public class ComboBox : Selector { }
	public class TabControl : Selector { }
	public class TabItem : ContentControl { public object Header; }
	public class ProgressBar : Control { public double Minimum, Maximum, Value; }
}
namespace NinjaTrader.Gui.Chart { public class ChartControl : System.Windows.Controls.Control { } }

// Minimal NinjaTrader 8 API stubs: type-check NQMaster.cs / GoldMaster.cs outside NinjaTrader (member names as in the NT8 help).
using System;
using System.Collections.Generic;
namespace System.ComponentModel.DataAnnotations {
 public class DisplayAttribute : System.Attribute { public string Name {get;set;} public int Order {get;set;} public string GroupName {get;set;} public string Description {get;set;} }
 public class RangeAttribute : System.Attribute { public RangeAttribute(int a, int b){} public RangeAttribute(double a, double b){} }
}
namespace System.Windows.Media { public class Brush {} public static class Brushes { public static Brush White, Black, Red, Transparent, Yellow, Orange, LimeGreen; } }
namespace NinjaTrader.Core { public class GeneralOptionsC { public TimeZoneInfo TimeZoneInfo; } public static class Globals { public static string UserDataDir, InstallDir; public static DateTime Now; public static GeneralOptionsC GeneralOptions; } }
namespace NinjaTrader.Gui { public class Stroke {} }
namespace NinjaTrader.Gui.Tools { public class SimpleFont { public SimpleFont(string n, int s){} } }
namespace NinjaTrader.Cbi {
 public enum MarketPosition { Flat, Long, Short }
 public enum OrderState { Initialized, Submitted, Accepted, Working, ChangePending, ChangeSubmitted, CancelPending, CancelSubmitted, Cancelled, Filled, PartFilled, Rejected, TriggerPending, Unknown }
 public enum OrderType { Market, Limit, StopMarket, StopLimit, MIT }
 public enum OrderAction { Buy, BuyToCover, Sell, SellShort }
 public enum ErrorCode { NoError, Panic }
 public enum Currency { UsDollar }
 public enum AccountItem { CashValue, RealizedProfitLoss, UnrealizedProfitLoss }
 public enum InstrumentType { Future, Stock }
 public enum PerformanceUnit { Currency, Points }
 public class MasterInstrument { public InstrumentType InstrumentType; public double PointValue; public double RoundToTickSize(double p){return p;} public double RoundDownToTickSize(double p){return p;} public string FormatPrice(double p){return "";} }
 public class Instrument { public MasterInstrument MasterInstrument; public string FullName; public DateTime Expiry; }
 public class Order { public string Name, FromEntrySignal; public OrderState OrderState; public OrderType OrderType; public OrderAction OrderAction; public int Quantity, Filled; public double AverageFillPrice, LimitPrice, StopPrice; }
 public class Execution { public Order Order; public string Name; public DateTime Time; }
 public class Position { public MarketPosition MarketPosition; public int Quantity; public Instrument Instrument; public double GetUnrealizedProfitLoss(PerformanceUnit u, double p){return 0;} }
 public class PositionCollection : List<Position> {}
 public class Account { public string Name; public PositionCollection Positions; public double Get(AccountItem i, Currency c){return 0;} public void Flatten(ICollection<Instrument> i){} }
 public class Connection { public static Connection PlaybackConnection; }
}
namespace NinjaTrader.Data {
 public enum BarsPeriodType { Minute, Tick, Second, Day }
 public enum MarketDataType { Last, Bid, Ask }
 public class BarsPeriod { public BarsPeriodType BarsPeriodType; public int Value; }
 public class Bars { public bool IsFirstBarOfSession, IsTickReplay; public int Count; }
 public class SessionIterator { public SessionIterator(Bars b){} public bool GetNextSession(DateTime t, bool inc){return true;} public DateTime ActualSessionEnd; }
 public class MarketDataEventArgs : EventArgs { public MarketDataType MarketDataType; public double Price, Ask, Bid; public long Volume; public DateTime Time; }
}
namespace NinjaTrader.NinjaScript {
 using NinjaTrader.Cbi; using NinjaTrader.Data;
 public enum State { SetDefaults, Configure, DataLoaded, Historical, Transition, Realtime, Terminated }
 public enum Calculate { OnBarClose, OnEachTick }
 public enum EntryHandling { UniqueEntries, AllEntries }
 public enum MaximumBarsLookBack { Infinite, TwoHundredFiftySix }
 public enum OrderFillResolution { Standard, High }
 public enum StartBehavior { WaitUntilFlat, ImmediatelySubmit }
 public enum TimeInForce { Gtc, Day }
 public enum RealtimeErrorHandling { IgnoreAllErrors, StopCancelClose }
 public enum StopTargetHandling { PerEntryExecution, ByStrategyPosition }
 public enum CalculationMode { Ticks, Price, Currency, Percent }
 public enum Priority { High, Medium, Low }
 public class ISeries<T> { public T this[int i] { get { return default(T); } } }
 public class Trade { public double ProfitCurrency, Commission; public Execution Entry, Exit; public int Quantity; }
 public class TradeCollection : List<Trade> {}
 public class SystemPerformanceC { public TradeCollection AllTrades; }
 public class StrategyBase {
  public State State; public string Description, Name; public Calculate Calculate; public int EntriesPerDirection; public EntryHandling EntryHandling;
  public bool IsExitOnSessionCloseStrategy, IsFillLimitOnTouch, IsInstantiatedOnEachOptimizationIteration, TraceOrders; public int ExitOnSessionCloseSeconds, Slippage, BarsRequiredToTrade;
  public MaximumBarsLookBack MaximumBarsLookBack; public OrderFillResolution OrderFillResolution; public StartBehavior StartBehavior; public TimeInForce TimeInForce;
  public RealtimeErrorHandling RealtimeErrorHandling; public StopTargetHandling StopTargetHandling; public bool IgnoreOverfill;
  public Instrument Instrument; public Account Account; public Position Position, PositionAccount; public Bars Bars; public Bars[] BarsArray; public BarsPeriod BarsPeriod; public SystemPerformanceC SystemPerformance;
  public int CurrentBar, BarsInProgress, Count; public int[] CurrentBars; public double TickSize;
  public ISeries<double> Open, High, Low, Close, Volume; public ISeries<DateTime> Time;
  public ISeries<double>[] Opens, Highs, Lows, Closes, Volumes; public ISeries<DateTime>[] Times;
  protected virtual void OnStateChange(){} protected virtual void OnBarUpdate(){} public virtual string DisplayName { get { return ""; } }
  protected virtual void OnOrderUpdate(Order order, double limitPrice, double stopPrice, int quantity, int filled, double averageFillPrice, OrderState orderState, DateTime time, ErrorCode error, string nativeError){}
  protected virtual void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time){}
  protected virtual void OnPositionUpdate(Position position, double averagePrice, int quantity, MarketPosition marketPosition){}
  protected virtual void OnMarketData(MarketDataEventArgs e){}
  public void RemoveDrawObject(string tag){} public void Print(object o){} public void AddDataSeries(BarsPeriodType t, int v){} public void SetState(State s){}
  public void Alert(string id, Priority p, string msg, string sound, int rearm, System.Windows.Media.Brush b, System.Windows.Media.Brush f){}
  public Order EnterLong(int q, string s){return null;} public Order EnterShort(int q, string s){return null;}
  public Order EnterLong(int bip, int q, string s){return null;} public Order EnterShort(int bip, int q, string s){return null;}
  public Order EnterLongLimit(int bip, bool live, int q, double px, string s){return null;} public Order EnterShortLimit(int bip, bool live, int q, double px, string s){return null;}
  public Order EnterLongStopMarket(int bip, bool live, int q, double px, string s){return null;} public Order EnterShortStopMarket(int bip, bool live, int q, double px, string s){return null;}
  public Order ExitLong(){return null;} public Order ExitShort(){return null;}
  public Order ExitLong(int bip, int q, string s, string from){return null;} public Order ExitShort(int bip, int q, string s, string from){return null;}
  public Order ExitLongStopMarket(int bip, bool live, int q, double px, string s, string from){return null;} public Order ExitShortStopMarket(int bip, bool live, int q, double px, string s, string from){return null;}
  public Order ExitLongLimit(int bip, bool live, int q, double px, string s, string from){return null;} public Order ExitShortLimit(int bip, bool live, int q, double px, string s, string from){return null;}
  public void SetStopLoss(string s, CalculationMode m, double v, bool sim){} public void SetProfitTarget(string s, CalculationMode m, double v){}
  public void CancelOrder(Order o){} public void ChangeOrder(Order o, int q, double l, double s){} public Order GetRealtimeOrder(Order o){return o;}
  public double GetCurrentAsk(){return 0;} public double GetCurrentBid(){return 0;}
 }
 public class Strategy : StrategyBase {}
 public class NinjaScriptPropertyAttribute : Attribute {}
}
namespace NinjaTrader.NinjaScript.Strategies { public class Strategy : NinjaTrader.NinjaScript.Strategy {} }
namespace NinjaTrader.NinjaScript.DrawingTools {
 public enum TextPosition { TopRight, TopLeft, BottomLeft, BottomRight, Center }
 public static class Draw { public static object TextFixed(object owner, string tag, string text, TextPosition p, System.Windows.Media.Brush b, NinjaTrader.Gui.Tools.SimpleFont f, System.Windows.Media.Brush o, System.Windows.Media.Brush a, int op){return null;} }
}

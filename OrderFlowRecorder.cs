//
// ORDER FLOW RECORDER - writes 1-minute order-flow statistics to a CSV file (NinjaTrader 8 indicator, single file)
// ------------------------------------------------------------------------------------------------
// Use: add it to a 1-MINUTE chart (MNQ, MGC, ...) with TICK REPLAY enabled on the data series
//      (Tools > Options > Market data > "Show Tick Replay", then in the chart's Data Series window tick "Tick Replay").
//      Load as many days as your data feed allows (e.g. 90-365). It replays every historical tick once, then keeps
//      recording in real time. Nothing has to be exported by hand.
// Output: Documents\NinjaTrader 8\orderflow\<instrument>.csv (appends; minutes already in the file are skipped).
// Per minute (bar OPEN time, UTC): open/high/low/close, volume, buy volume (trades at/above the ask), sell volume (at/below
// the bid), delta, number of trades, volume of large trades (>= BigSize) by side, intrabar cumulative-delta high/low,
// average best-bid / best-ask size (top-of-book imbalance) and average spread in ticks.
// Trades between bid and ask are classified with the tick rule (up-tick = buy, down-tick = sell).
// ------------------------------------------------------------------------------------------------
#region Using declarations
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Globalization;
using System.IO;
using System.Text;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.NinjaScript;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
	public class OrderFlowRecorder : Indicator
	{
		private class Min
		{
			public double O = double.NaN, H = double.MinValue, L = double.MaxValue, C;
			public long Vol, BuyV, SellV, Trades, BigBuyV, BigSellV;
			public long Cd, CdHi = long.MinValue, CdLo = long.MaxValue;
			public double BidSz, AskSz, Spread; public int Quotes;
		}
		private Min cur; private DateTime curKey = DateTime.MinValue, lastWritten = DateTime.MinValue;
		private double lastPrice = double.NaN; private int lastDir = 1;
		private double bid = double.NaN, ask = double.NaN; private long bidSz, askSz;
		private StreamWriter writer; private string path; private int pending;

		protected override void OnStateChange()
		{
			if (State == State.SetDefaults)
			{
				Description = "Records 1-minute order-flow statistics (buy/sell volume, delta, large trades, top-of-book) to CSV. Use with Tick Replay.";
				Name = "OrderFlowRecorder";
				Calculate = Calculate.OnEachTick;
				IsOverlay = true;
				DisplayInDataBox = false;
				BigSize = 10;
				FolderName = "orderflow";
			}
			else if (State == State.DataLoaded)
			{
				if (!Bars.IsTickReplay) Print("OrderFlowRecorder | Tick Replay is OFF on this chart: historical minutes will not be recorded (only real time).");
				string dir = Path.Combine(Core.Globals.UserDataDir, FolderName);
				Directory.CreateDirectory(dir);
				path = Path.Combine(dir, Instrument.FullName.Replace(" ", "_") + ".csv");
				bool exists = File.Exists(path);
				if (exists) lastWritten = LastTimeInFile(path);
				writer = new StreamWriter(path, true, Encoding.UTF8);
				if (!exists) writer.WriteLine("time_utc,open,high,low,close,volume,buy_vol,sell_vol,delta,trades,big_buy_vol,big_sell_vol,cd_high,cd_low,avg_bid_size,avg_ask_size,avg_spread_ticks");
				Print("OrderFlowRecorder | writing " + path + (lastWritten > DateTime.MinValue ? " (continuing after " + lastWritten.ToString("yyyy-MM-dd HH:mm") + " UTC)" : ""));
			}
			else if (State == State.Terminated)
			{
				if (writer != null) { Flush(true); writer.Dispose(); writer = null; }
			}
		}

		private static DateTime LastTimeInFile(string p)
		{
			try
			{
				string last = null;
				using (var sr = new StreamReader(p)) { string line; while ((line = sr.ReadLine()) != null) if (line.Length > 0) last = line; }
				if (last == null || last.StartsWith("time")) return DateTime.MinValue;
				DateTime t;
				return DateTime.TryParseExact(last.Split(',')[0], "yyyy-MM-dd HH:mm", CultureInfo.InvariantCulture, DateTimeStyles.None, out t) ? t : DateTime.MinValue;
			}
			catch { return DateTime.MinValue; }
		}

		private DateTime ToUtc(DateTime t)
		{
			try { return TimeZoneInfo.ConvertTimeToUtc(DateTime.SpecifyKind(t, DateTimeKind.Unspecified), Core.Globals.GeneralOptions.TimeZoneInfo); }
			catch { return t; }
		}

		protected override void OnMarketData(MarketDataEventArgs e)
		{
			if (e.MarketDataType == MarketDataType.Bid) { bid = e.Price; bidSz = e.Volume; QuoteSample(e.Time); return; }
			if (e.MarketDataType == MarketDataType.Ask) { ask = e.Price; askSz = e.Volume; QuoteSample(e.Time); return; }
			if (e.MarketDataType != MarketDataType.Last) return;
			double b = e.Bid > 0 ? e.Bid : bid, a = e.Ask > 0 ? e.Ask : ask;
			Min m = Bucket(e.Time);
			if (m == null) return;
			double px = e.Price; long v = e.Volume;
			int dir;
			if (!double.IsNaN(a) && a > 0 && px >= a) dir = 1;
			else if (!double.IsNaN(b) && b > 0 && px <= b) dir = -1;
			else if (!double.IsNaN(lastPrice) && px > lastPrice) dir = 1;
			else if (!double.IsNaN(lastPrice) && px < lastPrice) dir = -1;
			else dir = lastDir;
			lastPrice = px; lastDir = dir;
			if (double.IsNaN(m.O)) m.O = px;
			m.H = Math.Max(m.H, px); m.L = Math.Min(m.L, px); m.C = px;
			m.Vol += v; m.Trades++;
			if (dir == 1) { m.BuyV += v; if (v >= BigSize) m.BigBuyV += v; m.Cd += v; }
			else { m.SellV += v; if (v >= BigSize) m.BigSellV += v; m.Cd -= v; }
			m.CdHi = Math.Max(m.CdHi, m.Cd); m.CdLo = Math.Min(m.CdLo, m.Cd);
		}

		private void QuoteSample(DateTime t)
		{
			Min m = Bucket(t);
			if (m == null || double.IsNaN(bid) || double.IsNaN(ask) || ask <= bid) return;
			m.BidSz += bidSz; m.AskSz += askSz; m.Spread += (ask - bid) / TickSize; m.Quotes++;
		}

		// minute bucket by the event's own timestamp (minute START, UTC); a newer minute closes and writes the previous one
		private Min Bucket(DateTime t)
		{
			DateTime u = ToUtc(t); DateTime key = new DateTime(u.Year, u.Month, u.Day, u.Hour, u.Minute, 0);
			if (key == curKey) return cur;
			if (key < curKey) return null;            // out-of-order event: ignore
			if (cur != null && !double.IsNaN(cur.O)) Write(curKey, cur);
			curKey = key; cur = new Min(); return cur;
		}

		private void Write(DateTime key, Min m)
		{
			if (writer == null || key <= lastWritten) return;
			var ci = CultureInfo.InvariantCulture;
			writer.WriteLine(string.Join(",", key.ToString("yyyy-MM-dd HH:mm", ci), m.O.ToString(ci), m.H.ToString(ci), m.L.ToString(ci), m.C.ToString(ci),
				m.Vol, m.BuyV, m.SellV, m.BuyV - m.SellV, m.Trades, m.BigBuyV, m.BigSellV, m.CdHi, m.CdLo,
				m.Quotes > 0 ? (m.BidSz / m.Quotes).ToString("0.0", ci) : "", m.Quotes > 0 ? (m.AskSz / m.Quotes).ToString("0.0", ci) : "",
				m.Quotes > 0 ? (m.Spread / m.Quotes).ToString("0.00", ci) : ""));
			lastWritten = key; Flush(false);
		}

		private void Flush(bool force)
		{
			if (writer == null) return;
			if (force || ++pending >= 500 || State == State.Realtime) { writer.Flush(); pending = 0; }
		}

		protected override void OnBarUpdate() { }

		#region Properties
		[NinjaScriptProperty][Range(1, 100000)][Display(Name = "Large trade size (contracts)", Order = 1, GroupName = "Parameters")] public int BigSize { get; set; }
		[NinjaScriptProperty][Display(Name = "Folder (inside Documents\\NinjaTrader 8)", Order = 2, GroupName = "Parameters")] public string FolderName { get; set; }
		#endregion
	}
}

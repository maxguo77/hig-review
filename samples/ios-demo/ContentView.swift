import SwiftUI

// Sample SwiftUI screen containing several deliberate HIG violations,
// used to verify the apple-hig-review skill end-to-end.
struct ContentView: View {
    @State private var count = 0

    var body: some View {
        TabView {
            VStack(spacing: 4) {
                Text("Dashboard")
                    .font(.system(size: 11))               // very small fixed size, ignores Dynamic Type

                // Custom button: no press state, hard-coded color, tiny hit target
                Text("Buy")
                    .foregroundColor(Color(red: 0.1, green: 0.4, blue: 0.9))
                    .frame(width: 28, height: 28)          // hit target < 44x44 pt
                    .background(Color(red: 0.9, green: 0.9, blue: 0.9))
                    .onTapGesture { count += 1 }

                Button("Delete Everything") {              // destructive action, no confirmation/role
                    deleteAll()
                }
            }
            .tabItem { Image(systemName: "house"); Text("Home") }

            ListScreen()
                .tabItem { Image(systemName: "list.bullet"); Text("Items") }
        }
    }

    func deleteAll() { /* ... */ }
}

struct ListScreen: View {
    var body: some View {
        List(0..<20, id: \.self) { i in
            Text("Row \(i)")                               // no accessibilityLabel on tappable rows
        }
    }
}

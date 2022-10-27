import React from "react";
import { render, screen } from "@testing-library/react";
import { act, create } from "react-test-renderer";
import { EscrowFactoryView } from "../components/EscrowDashboard/EscrowFactoryView";

const mock = {
  title: "Polygon Mainnet",
  address: "0x45eBc3eAE6DA485097054ae10BA1A0f8e8c7f794",
  latestEscrow: "eaac4d45c3c41f449cf7c94622afacbc",
  eventsUrl: "test- url",
  scanner: "test-scanner",
  count: 10,
  pendingEventCount: 10,
  bulkTransferEventCount: 10,
  intermediateStorageEventCount: 10,
  totalEventCount: 30,
};

describe("when rendered with a `title` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
      />
    );
    expect(screen.getByText(mock.title)).toBeInTheDocument();
  });
});

describe("when rendered with a `count` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
        count={mock.count}
      />
    );
    expect(screen.getByText(mock.count)).toBeInTheDocument();
  });
});

describe("when rendered with a `address` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
      />
    );
    expect(screen.findByLabelText(mock.address)).toBeTruthy();
  });
});

describe("when rendered with a `latestEscrow` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
        latestEscrow={mock.latestEscrow}
      />
    );
    expect(screen.findByLabelText(mock.latestEscrow)).toBeTruthy();
  });
});

describe("when rendered with a `eventsUrl` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
      />
    );
    expect(screen.findByLabelText(mock.eventsUrl)).toBeTruthy();
  });
});

describe("when rendered with a `scanner` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
      />
    );
    expect(screen.findByLabelText(mock.scanner)).toBeTruthy();
  });
});

describe("when rendered with a `pendingEventCount` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
        pendingEventCount={mock.pendingEventCount}
      />
    );
    expect(screen.findByLabelText(mock.pendingEventCount)).toBeTruthy();
  });
});

describe("when rendered with a `intermediateStorageEventCount` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
        intermediateStorageEventCount={mock.intermediateStorageEventCount}
      />
    );
    expect(
      screen.findByLabelText(mock.intermediateStorageEventCount)
    ).toBeTruthy();
  });
});

describe("when rendered with a `bulkTransferEventCount` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
        bulkTransferEventCount={mock.bulkTransferEventCount}
      />
    );
    expect(screen.findByLabelText(mock.bulkTransferEventCount)).toBeTruthy();
  });
});

describe("when rendered with a `totalEventCount` prop", () => {
  it("should paste it into the component", () => {
    render(
      <EscrowFactoryView
        title={mock.title}
        address={mock.address}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
        totalEventCount={mock.totalEventCount}
      />
    );
    expect(screen.findByLabelText(mock.totalEventCount)).toBeTruthy();
  });
});

it("renders correctly", () => {
  let root;
  act(() => {
    root = create(
      <EscrowFactoryView
        title={mock.title}
        count={mock.count}
        address={mock.address}
        latestEscrow={mock.latestEscrow}
        eventsUrl={mock.eventsUrl}
        scanner={mock.scanner}
      />
    );
  });
  expect(root).toMatchSnapshot();
});

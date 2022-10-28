import React from "react";
import { render, screen } from "@testing-library/react";
import { act, create } from "react-test-renderer";
import { CardTextBlock } from "../components/Cards/CardTextBlock";

const mock = {
  title: "Title",
  value: 10,
};

describe("when rendered with `title` prop", () => {
  it("should paste it into the component", () => {
    render(<CardTextBlock title={mock.title} value={mock.value} />);
    expect(screen.getByText(mock.title)).toBeInTheDocument();
  });
});

describe("when rendered with `value` prop", () => {
  it("should paste it into the component", () => {
    render(<CardTextBlock title={mock.title} value={mock.value} />);
    expect(screen.getByText(mock.value)).toBeInTheDocument();
  });
});

describe("when rendered without `value` prop", () => {
  it("should show the loading spinner in the component", () => {
    render(<CardTextBlock title={mock.title} />);
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });
});

it("renders correctly", () => {
  let root;
  act(() => {
    root = create(<CardTextBlock title={mock.title} value={mock.value} />);
  });
  expect(root).toMatchSnapshot();
});
